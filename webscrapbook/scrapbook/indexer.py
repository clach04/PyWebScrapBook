"""Generator to generate item metadata from files.
"""
import os
import shutil
import zipfile
import io
import mimetypes
import binascii
import re
from base64 import b64encode
from urllib.parse import urlsplit, unquote
from urllib.request import urlopen
from urllib.error import URLError
from datetime import datetime, timezone, timedelta

from lxml import etree

from .. import util
from ..util import Info


FIND_INDEX_EXT = {'.html', '.htz', '.maff', '.htm'}

HTML_TITLE_EXCLUDE_PARENTS = {
    'xmp',
    'svg',
    'template',
    }

REGEX_IE_DOC_COMMENT = re.compile(r'^\s*saved from url=\((\d+)\)(\S+)\s*')

REGEX_SF_DOC_COMMENT = re.compile(r'^\s+Page saved with SingleFile\s+url: (\S+)\s+saved date: ([^()]+)')

REGEX_MAOXIAN_DOC_COMMENT = re.compile(r'^\s*OriginalSrc: (\S+)')

REGEX_JS_DATE = re.compile(r'^([^()]+)')


def generate_item_title(book, id):
    # infer from source
    if book.meta[id].get('source'):
        parts = urlsplit(book.meta[id].get('source'))
        if parts.scheme:
            title = os.path.basename(unquote(parts.path))
            if title:
                return title

    return None


def generate_item_create(book, id):
    # infer from standard timestamp ID
    dt = util.id_to_datetime(id)
    if dt:
        return util.datetime_to_id(dt)

    # infer from ctime of index file
    index = book.meta[id].get('index')
    if index:
        file = os.path.join(book.data_dir, index)
        try:
            ts = os.stat(file).st_ctime
        except OSError:
            pass
        else:
            dt = datetime.fromtimestamp(ts)
            return util.datetime_to_id(dt)

    # infer from modify
    modify = book.meta[id].get('modify')
    if modify:
        return modify


def generate_item_modify(book, id):
    # infer from mtime of index file
    index = book.meta[id].get('index')
    if index:
        file = os.path.join(book.data_dir, index)
        try:
            ts = os.stat(file).st_mtime
        except OSError:
            pass
        else:
            dt = datetime.fromtimestamp(ts)
            return util.datetime_to_id(dt)

    # infer from create (and then ID)
    create = book.meta[id].get('create')
    if create:
        return create


def iter_title_elems(tree):
    """Iterate over valid title elements."""
    def check(elem):
        p = elem.getparent()
        while p is not None:
            if p.tag in HTML_TITLE_EXCLUDE_PARENTS:
                return False
            p = p.getparent()
        return True

    for elem in tree.iter('title'):
        if check(elem):
            yield elem


def iter_favicon_elems(tree):
    """Iterate over valid favicon elements."""
    for elem in tree.iter('link'):
        if 'icon' in elem.attrib.get('rel').lower().split():
            yield elem


class Indexer:
    """A class that generates item metadata for files.
    """
    def __init__(self, book, *,
            handle_ie_meta=True,
            handle_singlefile_meta=True,
            handle_savepagewe_meta=True,
            handle_maoxian_meta=True,
            ):
        self.book = book
        self.handle_ie_meta = handle_ie_meta
        self.handle_singlefile_meta = handle_singlefile_meta
        self.handle_savepagewe_meta = handle_savepagewe_meta
        self.handle_maoxian_meta = handle_maoxian_meta

    def run(self, files):
        self.book.load_meta_files()

        indexed = {}
        for file in files:
            id = yield from self._index_file(file)
            if id:
                yield Info('info', f'Added item "{id}" for "{self.book.get_subpath(file)}".')
                indexed[id] = True

        return indexed

    def _index_file(self, file):
        subpath = self.book.get_subpath(file)
        yield Info('debug', f'Indexing "{subpath}"...')

        if not os.path.isfile(file):
            yield Info('error', f'File "{subpath}" does not exist.')
            return None

        _, ext = os.path.splitext(file.lower())
        is_webpage = ext in FIND_INDEX_EXT

        if is_webpage:
            tree = self.book.get_tree_from_index_file(file)
            if tree is None:
                yield Info('error', f'Failed to read document from file "{subpath}"')
                return None

            tree_root = tree.getroot()
            html_elem = tree_root if tree_root.tag == 'html' else None
            if html_elem is None:
                yield Info('error', f'No html element in file "{subpath}"')
                return None

        # generate default properties
        meta = self.book.DEFAULT_META.copy()

        if is_webpage:
            # attempt to load metadata generated by certain applications
            if self.handle_ie_meta:
                self._handle_ie_meta(meta, tree_root)

            if self.handle_singlefile_meta:
                self._handle_singlefile_meta(meta, tree_root)

            if self.handle_savepagewe_meta:
                self._handle_savepagewe_meta(meta, tree_root)

            if self.handle_maoxian_meta:
                self._handle_maoxian_meta(meta, tree_root)

            # merge properties from html[data-scrapbook-*] attributes
            for key, value in html_elem.attrib.items():
                if key.startswith(self.book.META_PROPERTY_PREFIX):
                    meta[key[len(self.book.META_PROPERTY_PREFIX):]] = value

        # id
        id = meta.pop('id')
        if id:
            # if explicitly specified in html attributes, use it or fail out.
            if id in self.book.meta:
                yield Info('error', f'Specified ID "{id}" is already used.')
                return None

            if id in self.book.SPECIAL_ITEM_ID:
                yield Info('error', f'Specified ID "{id}" is invalid.')
                return None

        else:
            # Take base filename as id if it corresponds to standard timestamp
            # format and not used; otherwise generate a new one.
            basepath = os.path.relpath(file, self.book.data_dir)
            basename = os.path.basename(basepath)
            if basename == 'index.html':
                basename = os.path.basename(os.path.dirname(basepath))
            id, _ = os.path.splitext(basename)

            if not util.id_to_datetime(id) or id in self.book.meta:
                ts = datetime.now(timezone.utc)
                id = util.datetime_to_id(ts)
                while id in self.book.meta:
                    ts += timedelta(milliseconds=1)
                    id = util.datetime_to_id(ts)

        # add to meta
        self.book.meta[id] = meta

        # index
        meta['index'] = index = os.path.relpath(file, self.book.data_dir).replace('\\', '/')

        # type
        if not meta['type']:
            meta['type'] = '' if is_webpage else 'file'

        # title
        if meta['title'] is None:
            title = None
            if is_webpage:
                title_elem = next(iter_title_elems(tree), None)
                if title_elem is not None:
                    try:
                        title = ((title_elem.text or '') +
                            ''.join(etree.tostring(e, encoding='unicode') for e in title_elem))
                    except UnicodeDecodeError as exc:
                        yield Info('error', f'Failed to extract title for "{id}": {exc}')
            if not title or not title.strip():
                title = generate_item_title(self.book, id)
            meta['title'] = title or ''

        # create
        if not meta['create']:
            meta['create'] = generate_item_create(self.book, id) or ''

        # modify
        if not meta['modify']:
            meta['modify'] = generate_item_modify(self.book, id) or ''

        # icon
        if meta['icon'] is None:
            if is_webpage:
                favicon_elem = next(iter_favicon_elems(tree), None)
                icon = favicon_elem.attrib.get('href', '') if favicon_elem is not None else ''
                if icon and util.is_archive(index):
                    icon = yield from self._get_archive_favicon(id, index, icon)
                meta['icon'] = icon
            else:
                meta['icon'] = ''

        generator = FavIconCacher(self.book)
        yield from generator.run([id])

        # source
        if meta['source'] is None:
            meta['source'] = ''

        # comment
        if meta['comment'] is None:
            meta['comment'] = ''

        return id

    def _handle_ie_meta(self, meta, root):
        doc_comment = root.getprevious()

        if doc_comment is None:
            return

        if doc_comment.tag != etree.Comment:
            return

        m = REGEX_IE_DOC_COMMENT.search(doc_comment.text)
        if m is None:
            return

        length = m.group(1)
        source = m.group(2)
        try:
            if len(source) == int(length, 10):
                meta['source'] = source
        except ValueError:
            pass

    def _handle_singlefile_meta(self, meta, root):
        try:
            doc_comment = root[0]
        except KeyError:
            return

        if doc_comment.tag != etree.Comment:
            return

        m = REGEX_SF_DOC_COMMENT.search(doc_comment.text)
        if m is None:
            return

        source = m.group(1)
        date_str = m.group(2)
        dt = datetime.strptime(date_str, "%a %b %d %Y %H:%M:%S GMT%z ")

        meta['source'] = source
        meta['create'] = util.datetime_to_id(dt)

    def _handle_savepagewe_meta(self, meta, root):
        node = root.find('.//meta[@name="savepage-url"][@content]')
        if node is not None:
            meta['source'] = node.attrib['content']

        node = root.find('.//meta[@name="savepage-title"][@content]')
        if node is not None:
            meta['title'] = node.attrib['content']

        node = root.find('.//meta[@name="savepage-date"][@content]')
        if node is not None:
            m = REGEX_JS_DATE.match(node.attrib['content'])
            if m:
                dt = datetime.strptime(m.group(1), "%a %b %d %Y %H:%M:%S GMT%z ")
                meta['create'] = util.datetime_to_id(dt)

    def _handle_maoxian_meta(self, meta, root):
        try:
            doc_comment = root[0]
        except KeyError:
            return

        if doc_comment.tag != etree.Comment:
            return

        m = REGEX_MAOXIAN_DOC_COMMENT.search(doc_comment.text)
        if m is None:
            return

        source = m.group(1)

        meta['source'] = source

    def _get_archive_favicon(self, id, index, url):
        """Convert in-zip relative favicon path to data URL.
        """
        # skip invalid in-zip-path
        if url.startswith('../'):
            yield Info('debug', f'Failed to read archive favicon "{util.crop(url, 256)}" for "{id}": invalid ZIP path')
            return ''

        urlparts = urlsplit(url)

        # skip absolute URL
        if urlparts.scheme:
            yield Info('debug', f'Skipped reading archive favicon "{util.crop(url, 256)}" for "{id}": absolute URL')
            return url

        subpath = unquote(urlparts.path)
        mime, _ = mimetypes.guess_type(subpath)
        file = os.path.join(self.book.data_dir, index)

        if util.is_htz(index):
            try:
                with zipfile.ZipFile(file) as zh:
                    bytes_ = zh.read(subpath)
            except (OSError, zipfile.BadZipFile, KeyError) as exc:
                yield Info('debug', f'Failed to read archive favicon "{util.crop(url, 256)}" for "{id}": {exc}')

        elif util.is_maff(index):
            try:
                page = next(iter(util.get_maff_pages(file)), None)
                if not page:
                    return ''

                refpath = page.indexfilename
                if not refpath:
                    return ''

                subpath = os.path.join(os.path.dirname(refpath), subpath).replace('\\', '/')
                with zipfile.ZipFile(file) as zh:
                    bytes_ = zh.read(subpath)
            except (OSError, zipfile.BadZipFile, KeyError):
                yield Info('debug', f'Failed to read archive favicon "{util.crop(url, 256)}" for "{id}": {exc}')

        return f'data:{mime};base64,{b64encode(bytes_).decode("ascii")}'


class FavIconCacher:
    def __init__(self, book):
        self.book = book
        self.favicons = {}

    def run(self, item_ids=None):
        self.book.load_meta_files()
        cached = {}

        # handle all items if none specified
        for id in item_ids or self.book.meta:
            if id not in self.book.meta:
                continue

            cache_file = yield from self._cache_favicon(id)
            if cache_file:
                cached[id] = cache_file

        return cached

    def _cache_favicon(self, id):
        def verify_mime(mime):
            if not mime:
                yield Info('error', f'Unable to cache favicon "{util.crop(url, 256)}" for "{id}": unknown MIME type')
                return False

            if not mime.startswith('image/') or mime == 'application/octet-stream':
                yield Info('error', f'Unable to cache favicon "{util.crop(url, 256)}" for "{id}": invalid image MIME type "{mime}"')
                return False

            return True

        def cache_fh(fh):
            fsrc = io.BytesIO()
            while True:
                chunk = fh.read(8192)
                if not chunk:
                    break
                fsrc.write(chunk)

            fsrc.seek(0)
            hash_ = util.checksum(fsrc)
            ext = mimetypes.guess_extension(mime) or ''
            fdst = os.path.join(self.book.tree_dir, 'favicon', hash_ + ext)

            if os.path.isfile(fdst):
                yield Info('info', f'Use saved favicon for "{util.crop(url, 256)}" for "{id}" at "{self.book.get_subpath(fdst)}".')
                return fdst

            yield Info('info', f'Saving favicon "{util.crop(url, 256)}" for "{id}" at "{self.book.get_subpath(fdst)}".')
            fsrc.seek(0)
            os.makedirs(os.path.dirname(fdst), exist_ok=True)
            self.book.backup(fdst)
            with open(fdst, 'wb') as fw:
                shutil.copyfileobj(fsrc, fw)
            return fdst

        yield Info('debug', f'Caching favicon for "{id}"...')

        url = self.book.meta[id].get('icon')
        if not url:
            yield Info('debug', f'Skipped for "{id}": no favicon to cache.')
            return None

        urlparts = urlsplit(url)

        index = self.book.meta[id].get('index', '')

        # cache absolute URL (also works for data URL)
        if urlparts.scheme:
            try:
                r = urlopen(url)
            except URLError as exc:
                yield Info('error', f'Unable to cache favicon "{util.crop(url, 256)}" for "{id}": unable to fetch favicon URL.', exc=exc)
                return None
            except (ValueError, binascii.Error) as exc:
                yield Info('error', f'Unable to cache favicon "{util.crop(url, 256)}" for "{id}": unsupported or malformatted URL: {exc}', exc=exc)
                return None

            with r as r:
                mime, _ = util.parse_content_type(r.info()['content-type'])
                if not (yield from verify_mime(mime)):
                    return None

                cache_file = yield from cache_fh(r)

            self.book.meta[id]['icon'] = util.get_relative_url(
                cache_file,
                os.path.join(self.book.data_dir, os.path.dirname(index)),
                path_is_dir=False,
                )
            return cache_file

        return None
