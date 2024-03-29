from bs4 import BeautifulSoup

import analyzer
import css


class ListFilesTask(analyzer.Task):
    def run(self, context, report):
        context.set_property('html_files', [item for item in context.project_dir.glob('*.html') if item.is_file()])
        context.set_property('css_files', [item for item in context.project_dir.glob('*.css') if item.is_file()])


class ProjetNameTask(analyzer.Task):
    def run(self, context, report):
        report.append(context.project_name)
        return context.project_name


class CountHTMLFilesTask(analyzer.Task):
    def run(self, context, report):
        html_file_count = len(context.get_property('html_files'))
        report.append(html_file_count)
        return html_file_count


class CountCSSFilesTask(analyzer.Task):
    def run(self, context, report):
        report.append(len(context.get_property('css_files')))


class ExtractAuthorsTask(analyzer.Task):
    def run(self, context, report):
        authors = []

        for html_file in context.get_property('html_files'):
            soup = BeautifulSoup(html_file.read_text(), 'html.parser')

            author_meta = soup.find('meta', attrs={'name': 'author'})
            author = author_meta['content'].lower() if author_meta else None

            if author and 'robert cailliau' not in author not in authors:
                authors.append(author)

        report.append('|'.join(authors))


def _is_local_url(url):
    return (not url.startswith('http') and
            not url.startswith('#') and
            not url.startswith('data') and
            not url.startswith('.') and
            url.endswith('.html'))


class HyperlinkScoreTask(analyzer.ScoringTask):
    def score(self, context):
        pages = []
        urls = []

        # Extrait le nom des pages et les urls à partir des balises <a>
        for html_file in context.get_property('html_files'):
            pages.append(html_file.name.lower())

            soup = BeautifulSoup(html_file.read_text(), 'html.parser')
            for tag in soup.find_all('a'):
                if tag.get('href'):
                    urls.append(tag.get('href').strip().lower())

        # Vérifie la présence d'URL vers des pages externes.
        remote_urls = [url for url in urls if url.startswith('http')]
        self.score_if(len(remote_urls) > 0)

        # Nettoyage des urls internes
        local_urls = [url for url in urls if _is_local_url(url)]
        local_url_count = len(local_urls)

        # Vérifie l'absence d'urls de type file://
        local_urls = [url for url in local_urls if not url.startswith('file://')]
        self.score_if(len(local_urls) == local_url_count)

        # Vérifie l'absence de liens vers des pages locales inconnues
        unknown_pages = [url for url in local_urls if url not in pages]
        self.score_if(len(unknown_pages) == 0)

        # Vérifie que toutes les pages soient bien liées
        unlinked_pages = [page for page in pages if page not in local_urls]
        self.score_if(len(unlinked_pages) == 0)


class CheckIndexTask(analyzer.ScoringTask):
    """
    Vérifie si le fichier index.html existe bien
    """

    def score(self, context):
        self.score_if('index.html' in [file.name.lower() for file in context.get_property('html_files')])


class ImageScoreTask(analyzer.ScoringTask):
    def score(self, context):
        images = []

        # Extrait toutes les urls d'image.
        for html_file in context.get_property('html_files'):
            soup = BeautifulSoup(html_file.read_text(), 'html.parser')

            # check img tag
            for img in soup.find_all('img'):
                src = img.get('src')
                if src:
                    images.append(src.strip())

        # Vérifie l'absence de chemins locaux
        bad_src = [image for image in images if '\\' in image or image == '']
        self.score_if(len(bad_src) == 0)

        # Nettoyage de la liste des images et vérification qu'il en reste encore.
        images = [image for image in images if image != '']
        self.score_if(len(images) > 0)

        # Vérification que toutes les images aient bien été téléchargées.
        remote_images = [image for image in images if image.startswith('http')]
        self.score_if(len(remote_images) == 0)


def _get_tag_text(soup, tag, exclude=None):
    tag = soup.find(tag)
    if tag is None:
        return None

    text = tag.getText()
    if exclude and text in exclude:
        return None

    return text


class HTMLScoreTask(analyzer.ScoringTask):
    def score(self, context):
        page_count = len(context.get_property('html_files'))
        titles = []
        h1_tags = []
        page_without_paragraphe_count = 0

        for html_file in context.get_property('html_files'):
            soup = BeautifulSoup(html_file.read_text(), 'html.parser')

            forbidden_titles = ["Titre dans l'onglet du navigateur", "Titre d'une page secondaire"]
            title = _get_tag_text(soup, 'title', forbidden_titles)
            if title is not None:
                titles.append(title)

            forbidden_titles = ["Titre dans l'onglet du navigateur", "Titre d'une page secondaire"]
            title = _get_tag_text(soup, 'h1', forbidden_titles)
            if title is not None:
                h1_tags.append(title)

            if len(soup.find_all('p')) == 0:
                page_without_paragraphe_count += 1

        title_count = len(titles)
        self.score_if(title_count >= 1, amount=2)
        self.score_if(title_count == page_count)

        h1_count = len(h1_tags)
        self.score_if(h1_count >= 1, amount=2)
        self.score_if(h1_count == page_count)

        page_without_paragraphe_ratio = page_without_paragraphe_count * 100 / page_count if page_count > 0 else 0
        self.score_if(page_without_paragraphe_ratio <= 50)


class CSSScoreTask(analyzer.ScoringTask):
    def score(self, context):
        selectors = []
        already_exists = ['h2', '.texte-mis-en-forme-exemple', '.titre-page-exemple', '.petite-image-exemple', 'table',
                          'td']

        for css_file in context.get_property('css_files'):
            selectors += css.get_selectors(css_file.read_text())
        selectors = [item for item in selectors if item not in already_exists]
        type_selectors = [item for item in selectors if not item.startswith('.')]
        class_selectors = [item for item in selectors if item.startswith('.')]

        self.score_if(len(type_selectors) > 0)
        self.score_if(len(class_selectors) > 0, amount=2)
        self.score_if(len(selectors) >= 4, amount=2)
