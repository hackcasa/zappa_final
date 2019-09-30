from django.core.management.base import BaseCommand
from tqdm import tqdm
from web.models import Article, ArticleImage


class Command(BaseCommand):
    help = 'Link ArticleImages to Article'

    def handle(self, *args, **options):
        linked_count = 0
        article_not_found_count = 0
        unlinked_images = ArticleImage.objects.filter(
            article=None,
        )
        unlinked_count = unlinked_images.count()
        articles = Article.objects.all()

        for unlinked_image in tqdm(
                unlinked_images, total=unlinked_count):
            article = articles.filter(gtin=unlinked_image.gtin).first()

            if article is None:
                article_not_found_count += 1
            else:
                unlinked_image.article = article
                unlinked_image.save()
                linked_count += 1

        unlinked_images = ArticleImage.objects.filter(
            article=None,
        )

        print("*** REPORT ***")
        print(f"Items: {unlinked_count}")
        print(f"Linked: {linked_count}")
        print(f"Article not found count: {article_not_found_count}")
        print(f"Current unlinked image count: {unlinked_images.count()}")
