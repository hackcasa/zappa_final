from django.shortcuts import render, redirect
from web.models import Article, ArticleImage, Product, ProductImage, \
        ProductDetail, MerchantArticle, Tag, \
        ProductCategory
from web.forms import ArticleForm, ArticleSearchForm, \
        ArticleWhitelistForm, ArticleAllergensForm, \
        AllergenAddForm, ProductForm, ProductAllergensForm, \
        ProductImageAddForm, ProductImportCSVForm, \
        ProductSearchForm, ProductRecentChangesForm, MerchantArticleForm, \
        MerchantArticleSearchForm, TagForm, TagSearchForm, \
        ProductCategorySearchForm, ProductCategoryForm, \
        IncompleteProductSearchForm, TagsLinkForm, ProductDetailForm
from django.http import HttpResponse
from django.core import exceptions
from django.utils import timezone
from django.db.models import Q
from django.db.models import Value
from django.db.models.functions import Concat
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.templatetags.staticfiles import static
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from collections import defaultdict
import json
import boto3
import os
import csv
import re
import logging

logger = logging.getLogger(__name__)


@login_required
def home(request):
    logger.info("Dashboard view")
    product_changes = Product.history.all().order_by('-history_date')
    pagesize = request.GET.get('pagesize', 10)
    parameters = request.GET.copy()
    incomplete_products_count = Product.objects.filter(
                Q(valid_image=False) |
                Q(valid_brand=False) |
                Q(valid_price=False) |
                ~Q(article__vat__in=Article.VATS)).count()

    paginator = Paginator(product_changes, pagesize)
    page = request.GET.get('page')
    pagelist = paginator.get_page(page)

    return render(request, 'web/home.html',
                  {
                      'incomplete_products_count': incomplete_products_count,
                      'page': page,
                      'pagelist': pagelist,
                      'parameters': parameters,
                      'pagesize': int(pagesize),
                      'pagesizes': [10,25, 50, 100]
                  })


def login(request):
    return render(request, 'web/login.html',)


def logout(request):
    django_logout(request)

    if (request.GET.get('next')):
        return redirect('/login/?next=' + request.GET.get('next'))

    return redirect('/')


@login_required
def article_search(request):
    form = ArticleSearchForm()
    pagesize = request.GET.get('pagesize', 10)
    parameters = request.GET.copy()

    articles = Article.objects.filter(consumer_unit=True)

    if request.GET:
        form = ArticleSearchForm(request.GET)

        if form.is_valid():
            include_packages = form.cleaned_data['include_packages']
            only_complete = form.cleaned_data['only_complete']

            if include_packages and only_complete:
                articles = Article.objects.valid()
            elif include_packages and not only_complete:
                articles = Article.objects.all()
            elif not include_packages and only_complete:
                articles = Article.objects.valid().filter(consumer_unit=True)
            elif not include_packages and not only_complete:
                articles = Article.objects.filter(consumer_unit=True)

            articles = articles.filter(
                gtin__icontains=form.cleaned_data['gtin_input'],
                name__icontains=form.cleaned_data['name_input'],
                category__icontains=form.cleaned_data['category_input'],
                brand_name__icontains=form.cleaned_data['brand_name_input'],
                source__icontains=form.cleaned_data['source']
            )

            last_modified_start = form.cleaned_data[
                'last_modified_start_input']
            if last_modified_start is not None:
                articles = articles.filter(
                    last_modified__gte=last_modified_start)

            last_modified_end = form.cleaned_data[
                'last_modified_end_input']
            if last_modified_end is not None:
                last_modified_end_datetime = datetime.combine(
                    last_modified_end, datetime.max.time())
                articles = articles.filter(
                    last_modified__lte=last_modified_end_datetime)

    paginator = Paginator(articles, pagesize)
    page = request.GET.get('page')
    pagelist = paginator.get_page(page)

    return render(request, 'web/article.html',
                  {
                      'form': form,
                      'articles_length': paginator.count,
                      'parameters': parameters,
                      'pagesize': int(pagesize),
                      'pagelist': pagelist,
                      'pagesizes': [10, 25, 50, 100, 250]
                  })


@login_required
def article_details(request, gtin):
    article = Article.objects.get(gtin=gtin)

    related = article.get_related()

    child_label = article.child_gtin

    if article.child_gtin != "":
        child = Article.objects.filter(gtin=article.child_gtin).first()

        if child is not None:
            child_label = '<a href="/article/' + article.child_gtin + '/">' \
                + str(article.child_gtin) + '</a>'

    return render(request, 'web/article_details.html',
                  {
                      'article': article,
                      'child_label': child_label,
                      'related': related
                  })


@login_required
def article_edit(request, gtin):
    article = Article.objects.get(gtin=gtin)

    if article.source == "mathem":
        form = ArticleForm(instance=article)
    else:
        form = ArticleWhitelistForm(instance=article)

    if request.POST:
        if article.source == "mathem":
            form = ArticleForm(request.POST, instance=article)
        else:
            form = ArticleWhitelistForm(request.POST, instance=article)

        if form.is_valid():
            form.save()
            return redirect('article_details', gtin=article.gtin)

    return render(request, 'web/article_edit.html',
                  {
                    'article': article,
                    'form': form
                  })


@login_required
def article_allergens_edit(request, gtin):
    article = Article.objects.get(gtin=gtin)

    if article.source == "mathem":
        form = ArticleAllergensForm(instance=article)

        if request.POST:
            form = ArticleAllergensForm(request.POST, instance=article)

            if form.is_valid():
                form.save()
                return redirect('article_details', gtin=article.gtin)

        add_allergen_form = AllergenAddForm(auto_id=False)
        allergens = article.allergens
        return render(
            request,
            'web/article_allergens_edit.html',
            {
                'allergens': allergens,
                'add_allergen_form': add_allergen_form,
                'form': form,
                'article': article,
            })
    else:
        return redirect('article_details', gtin=article.gtin)


@login_required
def article_history(request, gtin):
    article = Article.objects.get(gtin=gtin)
    history = article.history.all()
    history_diffs = []
    old_record = False

    for historic_item in history:
        if old_record is False:
            old_record = historic_item
            continue

        delta = historic_item.diff_against(old_record)

        if delta.changes:
            history_diffs.append({
                'time': historic_item.history_date,
                'delta': delta.changes,
                'user': historic_item.history_user
            })

        old_record = historic_item

    return render(request, 'web/generic_history.html',
                  {
                      'model': "Article",
                      'generic': article,
                      'history': history_diffs,
                  })


@login_required
def article_image_history(request, id):
    image = ArticleImage.objects.get(pk=id)
    history = image.history.all()
    history_diffs = []
    old_record = False

    for historic_item in history:
        if old_record is False:
            old_record = historic_item
            continue

        delta = historic_item.diff_against(old_record)

        if delta.changes:
            history_diffs.append({
                'time': historic_item.history_date,
                'delta': delta.changes,
                'user': historic_item.history_user
            })

        old_record = historic_item

    return render(request, 'web/generic_history.html',
                  {
                      'model': "ArticleImage",
                      'generic': image,
                      'history': history_diffs,
                  })


@login_required
def product_recent(request):
    product_changes = Product.history.all().order_by('-history_date')
    pagesize = request.GET.get('pagesize', 25)
    parameters = request.GET.copy()

    if request.GET.get('product_name'):
        product_name_set = product_changes.filter(
            name__icontains=request.GET.get('product_name'))
        product_name_from_article_set = product_changes.filter(
            article__name__icontains=request.GET.get('product_name'),
            name='')
        product_changes = product_name_set | product_name_from_article_set

    if request.GET.get('changed_by'):
        product_changes = product_changes.annotate(
            full_name=Concat('history_user__first_name',
                             Value(' '),
                             'history_user__last_name'))

        product_changes = product_changes.filter(
            full_name__icontains=request.GET.get('changed_by'))

    if request.GET.get('gtin'):
        product_changes = product_changes.filter(
            article__gtin__icontains=request.GET.get('gtin'))

    if request.GET.get('changed_type', 'All') != 'All':
        product_changes = product_changes.filter(
            history_type=request.GET.get('changed_type')
        )

    paginator = Paginator(product_changes, pagesize)
    page = request.GET.get('page')
    pagelist = paginator.get_page(page)
    form = ProductRecentChangesForm(request.GET)
    return render(request, 'web/product_recent_changes.html',
                  {
                      'page': page,
                      'form': form,
                      'parameters': parameters,
                      'pagesize': int(pagesize),
                      'pagelist': pagelist,
                      'pagesizes': [25, 50, 100, 250]
                  })


@login_required
def product_incomplete(request):
    valid_vats = Article.VATS
    pagesize = request.GET.get('pagesize', 10)
    parameters = request.GET.copy()

    if request.GET:
        form = IncompleteProductSearchForm(request.GET)
        if form.is_valid():
            query = Q()
            if form.cleaned_data['include_invalid_image']:
                query |= Q(valid_image=False)
            if form.cleaned_data['include_invalid_brand']:
                query |= Q(valid_brand=False)
            if form.cleaned_data['include_invalid_price']:
                query |= Q(valid_price=False)
            if form.cleaned_data['include_invalid_vat']:
                query |= ~Q(article__vat__in=valid_vats)
            if form.cleaned_data['include_invalid_weight']:
                query |= Q(valid_weight=False)
            if form.cleaned_data['include_invalid_volume']:
                query |= Q(valid_volume=False)

            products = Product.objects.filter(query)

            if form.cleaned_data['product_id_input']:
                products = products.filter(
                    product_id__icontains=form.cleaned_data['product_id_input']
                )
            if form.cleaned_data['gtin_input']:
                products = products.filter(
                    article__gtin__icontains=form.cleaned_data['gtin_input']
                )
            if form.cleaned_data['product_name_input']:
                products = products.filter(
                    article__product__name__icontains=form.cleaned_data[
                        'product_name_input']
                )
            if form.cleaned_data['brand_name_input']:
                products = products.filter(
                    article__brand_name__icontains=form.cleaned_data[
                        'brand_name_input']
                )
            if form.cleaned_data['source']:
                products = products.filter(
                    article__source__icontains=form.cleaned_data[
                        'source']
                )
            if form.cleaned_data['tags']:
                products = products.filter(
                    tags__name__icontains=form.cleaned_data[
                        'tags']
                )

            last_modified_start = form.cleaned_data[
                'last_modified_start_input']
            if last_modified_start is not None:
                products = products.filter(
                    last_modified__gte=last_modified_start)

            last_modified_end = form.cleaned_data[
                'last_modified_end_input']
            if last_modified_end is not None:
                last_modified_end_datetime = datetime.combine(
                    last_modified_end, datetime.max.time())
                products = products.filter(
                    last_modified__lte=last_modified_end_datetime)
    else:
        form = IncompleteProductSearchForm()
        incomplete_products = Product.objects.filter(
            Q(valid_image=False) |
            Q(valid_brand=False) |
            Q(valid_price=False) |
            Q(valid_weight=False) |
            Q(valid_volume=False)
        )
        products = incomplete_products


    products_count = len(products)
    paginator = Paginator(products, pagesize)
    page = request.GET.get('page')
    pagelist = paginator.get_page(page)
    get_copy = request.GET.copy()
    if not request.GET:
        get_copy['include_invalid_vat'] = 'on'
        get_copy['include_invalid_image'] = 'on'
        get_copy['include_invalid_brand'] = 'on'
        get_copy['include_invalid_price'] = 'on'
        get_copy['include_invalid_weight'] = 'on'
        get_copy['include_invalid_volume'] = 'on'

    return render(request, 'web/product_incomplete.html',
                  {
                      'products_count': products_count,
                      'form': form,
                      'parameters': parameters,
                      'pagesize': int(pagesize),
                      'pagelist': pagelist,
                      'pagesizes': [10, 25, 50, 100, 250],
                      'valid_vats': valid_vats
                  })


@login_required
def product_index(request):
    form = ProductSearchForm(request.GET)
    pagesize = request.GET.get('pagesize', 10)
    parameters = request.GET.copy()

    products = Product.objects.filter(Product.valid_products_query)

    paginator = Paginator(products, pagesize)
    page = request.GET.get('page')
    pagelist = paginator.get_page(page)

    return render(request, 'web/product.html',
                  {
                      'form': form,
                      'products_length': paginator.count,
                      'parameters': parameters,
                      'pagesize': int(pagesize),
                      'pagelist': pagelist,
                      'pagesizes': [10, 25, 50, 100, 250]
                  })


@login_required
def product_search(request):
    form = ProductSearchForm(request.GET)
    pagesize = request.GET.get('pagesize', 10)
    parameters = request.GET.copy()
    products = Product.objects.filter(Product.valid_products_query)

    if form.is_valid():
        products = products.filter(
            product_id__icontains=form
            .cleaned_data['product_id_input'],
            article__gtin__icontains=form
            .cleaned_data['gtin_input'],
            article__product__name__icontains=form
            .cleaned_data['product_name_input'],
            article__brand_name__icontains=form
            .cleaned_data['brand_name_input'],
            article__source__icontains=form
            .cleaned_data['source'],
            tags__name__icontains=form
            .cleaned_data['tags']
        )

        last_modified_start = form.cleaned_data[
            'last_modified_start_input']
        if last_modified_start is not None:
            products = products.filter(
                last_modified__gte=last_modified_start)

        last_modified_end = form.cleaned_data[
            'last_modified_end_input']
        if last_modified_end is not None:
            last_modified_end_datetime = datetime.combine(
                last_modified_end, datetime.max.time())
            products = products.filter(
                last_modified__lte=last_modified_end_datetime)

    paginator = Paginator(products, pagesize)
    page = request.GET.get('page')
    pagelist = paginator.get_page(page)

    return render(request, 'web/product.html',
                  {
                      'form': form,
                      'products_length': paginator.count,
                      'parameters': parameters,
                      'pagesize': int(pagesize),
                      'pagelist': pagelist,
                      'pagesizes': [10, 25, 50, 100, 250]
                  })


@login_required
def product_allergens_copy(request, gtin):
    product = Product.objects.get(article__gtin=gtin)
    product.allergens = product.article.allergens
    product.save()

    return redirect('product_view', gtin=gtin)


@login_required
def product_allergens_edit(request, gtin):
    product = Product.objects.get(article__gtin=gtin)

    form = ProductAllergensForm(instance=product)

    if request.POST:
        form = ProductAllergensForm(request.POST, instance=product)

        if form.is_valid():
            form.save()
            return redirect('product_view', gtin=gtin)

    add_allergen_form = AllergenAddForm(auto_id=False)
    allergens = product.allergens

    return render(
        request,
        'web/product_allergens_edit.html',
        {
            'allergens': allergens,
            'add_allergen_form': add_allergen_form,
            'form': form,
            'product': product,
        })


@login_required
def product_history(request, gtin):
    product = Product.objects.get(article__gtin=gtin)
    history = product.history.all()
    history_diffs = []
    old_record = False

    for historic_item in history:
        if old_record is False:
            old_record = historic_item
            continue

        delta = historic_item.diff_against(old_record)

        if delta.changes:
            history_diffs.append({
                'time': historic_item.history_date,
                'delta': delta.changes,
                'user': historic_item.history_user
            })

        old_record = historic_item

    return render(request, 'web/generic_history.html',
                  {
                      'model': "Product",
                      'generic': product,
                      'history': history_diffs,
                  })


@login_required
def product_import(request):
    """Only products Articles that is not yet imported is
    possible to import"""
    if request.method == 'POST':

        gtins_list = request.POST.getlist('gtin_input')
        gtins = re.split(r'[,\s\n]+', ",".join(gtins_list))

        requested_articles = Article.objects.filter(gtin__in=gtins)

        already_imported = requested_articles.filter(
            gtin__in=list(Product.objects.values_list(
                'article__gtin',
                flat=True)
            )
        )

        not_consumer_unit = requested_articles.filter(consumer_unit=False)

        valid_articles = requested_articles.difference(
            already_imported | not_consumer_unit)

        not_found = set(gtins) - set(
            list(
                requested_articles.values_list(
                    'gtin',
                    flat=True
                )
            )
        )
        request_import = True
        valid_articles_gtin = valid_articles.values_list("gtin", flat=True)
    else:
        valid_articles = None
        valid_articles_gtin = None
        requested_articles = None
        request_import = False
        not_found = None
        already_imported = None
        not_consumer_unit = None

    import_csv_form = ProductImportCSVForm()
    csv_template = static('pim_import_template.csv')

    return render(request, 'web/product_import.html',
                  {
                      'valid_articles': valid_articles,
                      'valid_articles_gtin': valid_articles_gtin,
                      'requested_articles': requested_articles,
                      'request_import': request_import,
                      'not_found': not_found,
                      'already_imported': already_imported,
                      'not_consumer_unit': not_consumer_unit,
                      'import_csv_form': import_csv_form,
                      'csv_template': csv_template
                  })


@login_required
def product_import_csv(request):
    decoded_file = (
        request.FILES['filename']
        .read().decode('utf-8').splitlines())
    reader = csv.DictReader(decoded_file)
    errors = []
    report = defaultdict(list)
    update = request.POST.get('update_if_exists', False)

    # Validate we have the required fields
    keys_to_check = [
        'GTIN',
        'Name',
        'Brand',
        'Marketing message',
        'Ingredient Description',
        'Nutrition Description',
        'Price Stockholm',
        'Price Göteborg',
        'Price Malmö']

    for key in keys_to_check:
        if key not in reader.fieldnames:
            errors.append("Missing field: " + key)

    if len(errors) > 0:
        return render(
            request,
            'web/product_import_csv_report.html',
            {
                'errors': errors,
                'report': dict(report)
            })

    for item in reader:
        product_exists = True
        gtin = item['GTIN']
        article = Article.objects.filter(gtin=gtin).first()

        if article is None:
            report[gtin].append("No article found")
            continue

        product = Product.objects.filter(article__gtin=gtin).first()

        if product is None:
            # Create product
            product_exists = False
            product = Product(
                article=article
            )
            product.save()
            product.product_id = product.id
            product.save()

            # Create ProductDetails
            for line in ProductDetail.STORES:
                storeItem = ProductDetail(
                    store=line[0],
                    price=0,
                    enabled=True,
                    product=product
                )
                storeItem.save()

            # Get images from article
            for image in ArticleImage.objects.filter(gtin=gtin):
                new_image = ProductImage(
                    angle=image.angle,
                    source=image.source,
                    product=product,
                    filename=image.filename
                )
                new_image.save()

        if not update and product_exists:
            report[gtin].append("Product found. Not using update. Skipping")
            continue

        product.save()

        if item['Name']:
            if update or not product_exists:
                product.name = item['Name']
                report[gtin].append(
                    "Using name from file (" + item['Name'] + ")")
        else:
            report[gtin].append("Name not found in file")

        if item['Brand']:
            if update or not product_exists:
                product.brand_name = item['Brand']
                report[gtin].append(
                    "Using brand from file (" + item['Brand'] + ")")
        else:
            report[gtin].append("Brand not found in file")

        if item['Marketing message']:
            if update or not product_exists:
                product.marketing_message = item['Marketing message']
                report[gtin].append(
                    "Using marketing message from file (" +
                    item['Marketing message'] + ")")
        else:
            report[gtin].append("Marketing message not found in file")

        if item['Ingredient Description']:
            if update or not product_exists:
                product.ingredient_description = item['Ingredient Description']
                report[gtin].append(
                    "Using Ingredient Description from file (" +
                    item['Ingredient Description'] + ")")
        else:
            report[gtin].append("Ingredient Description not found in file")

        if item['Nutrition Description']:
            if update or not product_exists:
                product.nutrition_description = item['Nutrition Description']
                report[gtin].append(
                    "Using Nutrition Description from file (" +
                    item['Nutrition Description'] + ")")
        else:
            report[gtin].append("Nutrition Description not found in file")

        for details in product.product_detail.all():
            if details.store == 10:
                price = item['Price Stockholm']
            if details.store == 14:
                price = item['Price Göteborg']
            if details.store == 16:
                price = item['Price Malmö']

            if price and float(price) > 0:
                if update or not product_exists:
                    report[gtin].append(
                        "Price update on store " + str(details.store) +
                        " (" + str(details.price) + " => " + str(price) + ")")
                    details.price = price
                    details.save()
            else:
                report[gtin].append("Price not found in file")

        product.save()

    return render(
        request,
        'web/product_import_csv_report.html',
        {
            'errors': errors,
            'report': dict(report)
        })


@login_required
def product_add_gtin(request):
    if request.method == 'POST':
        created_items = 0
        last_gtin = str()

        gtins = request.POST.get('article_gtin').split(',')
        articles = Article.objects.filter(gtin__in=gtins)

        for article in articles:
            new_product = Product(
                article=article
            )
            new_product.save()
            new_product.product_id = new_product.id
            new_product.save()
            created_items = created_items + 1
            last_gtin = new_product.article.gtin

            # Set products default images
            for image in ArticleImage.objects.filter(gtin=article.gtin):
                new_image = ProductImage(
                    angle=image.angle,
                    source=image.source,
                    product=new_product,
                    filename=image.filename
                )
                new_image.save()

            # TODO setup store item for each store as well and save_m2m()
            for line in ProductDetail.STORES:
                storeItem = ProductDetail(
                    store=line[0],
                    price=0,
                    enabled=True,
                    product=new_product
                )
                storeItem.save()

    if(created_items == 1 and len(last_gtin) > 0):
        return redirect('/product/view/' + last_gtin)
    else:
        return redirect('/product/incomplete')


@login_required
def product_delete(request, gtin):
    """Delete product and ProductDetails"""
    _p = Product.objects.get(article__gtin=gtin)
    _pd = ProductDetail.objects.filter(product=_p)
    _pd.delete()
    _p.delete()
    return redirect('/product/')


@login_required
def product_image_history(request, id):
    image = ProductImage.objects.get(pk=id)
    history = image.history.all()
    history_diffs = []
    old_record = False

    for historic_item in history:
        if old_record is False:
            old_record = historic_item
            continue

        delta = historic_item.diff_against(old_record)

        if delta.changes:
            history_diffs.append({
                'time': historic_item.history_date,
                'delta': delta.changes,
                'user': historic_item.history_user
            })

        old_record = historic_item

    return render(request, 'web/generic_history.html',
                  {
                      'model': "ProductImage",
                      'generic': image,
                      'history': history_diffs,
                  })


@login_required
def product_image_toggle_active(request, id):
    image = ProductImage.objects.filter(pk=id).first()
    image.active = not image.active
    image.save()

    if request.GET.get('next') is not None:
        return redirect(request.GET.get('next'))

    return HttpResponse(status=204)


@login_required
def product_image_main(request, id):
    new_main_image = ProductImage.objects.filter(pk=id).first()
    new_main_image.main = True
    new_main_image.save()

    other_images = new_main_image.product.productimage_set.exclude(pk=id)
    for other_image in other_images:
        other_image.main = False
        other_image.save()

    if request.GET.get('next') is not None:
        return redirect(request.GET.get('next'))

    return HttpResponse(status=204)


@login_required
def product_image_add(request, gtin):
    if request.method == 'POST':
        form = ProductImageAddForm(request.POST, request.FILES)
        if form.is_valid():
            product = Product.objects.filter(
                article__gtin__icontains=gtin).first()
            if product is not None:
                file = request.FILES['filename']
                file_content = file.read()

                image_number = product.productimage_set.count() + 1

                image = ProductImage()
                image.source = 'mathem'
                image.product = product
                image.active = form.cleaned_data['active']
                image.filename = (product.article.gtin +
                                  "_" + str(image_number) + ".jpg")
                image.save()

                bucket_name = os.environ.get('pim-validoo-item-BucketName')

                if bucket_name is not None:
                    bucket_destination = 'in-product-image/' + image.filename
                    client = boto3.client('s3')
                    client.put_object(Body=file_content,
                                      Bucket=bucket_name,
                                      Key=bucket_destination)

                return redirect('/product/view/' + gtin + '#images')

    else:
        form = ProductImageAddForm()

    return render(request, 'web/product_image_add.html',
                  {
                      'gtin': gtin,
                      'form': form
                  })


@login_required
def product_image_delete(request, id):
    image = ProductImage.objects.get(pk=id)
    image.delete()

    if request.GET.get("next") is not None:
        return redirect(request.GET.get("next"))

    return HttpResponse(status=204)


@login_required
def article_add(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            _a = form.save(commit=False)
            _a.gtin = _a.gtin.zfill(14)
            _a.source = "mathem"
            _a.last_modified = datetime.now()
            _a.creation_date = datetime.now()
            _a.save()
            return redirect('/article/#new-article-'+_a.gtin)
    else:
        form = ArticleForm()

    return render(request, 'web/article_add.html',
                  {
                      'form': form,
                  })


@login_required
def product_view(request, gtin):
    valid_vats = Article.VATS

    product = Product.objects.get(article__gtin=gtin)
    try:
        product_detail = ProductDetail.objects.filter(
            product=product).order_by('store')
    except exceptions.ObjectDoesNotExist:
        product_detail = None
        pass

    return render(request, 'web/product_view.html',
                  {
                      'product': product,
                      'product_detail': product_detail,
                      'valid_vats': valid_vats
                  })


@login_required
def product_edit(request, gtin):

    product = Product.objects.get(article__gtin=gtin)
    form = ProductForm(instance=product)

    if request.POST:
        form = ProductForm(request.POST, instance=product)

        if form.is_valid():
            form.save()
            return redirect('product_view', gtin=gtin)

    return render(request, 'web/product_edit.html',
                  {
                      'form': form,
                      'product': product,
                      'gtin': gtin
                  })


@login_required
def product_detail_edit(request, id):
    detail = ProductDetail.objects.get(pk=id)
    form = ProductDetailForm(instance=detail)

    if form.instance.is_tagged_as_new():
        new_tag_stop = form.instance.first_enabled + timedelta(days=30)
        new_until_delta = (timezone.now()
                           - new_tag_stop)
        days_left_as_new = abs(new_until_delta.days)
        form.fields['new_product'].initial = True
        form.fields['new_product'].help_text = ("(For another "
                                                + str(days_left_as_new)
                                                + " days)")

    if request.method == 'POST':
        form = ProductDetailForm(request.POST, instance=detail)

        if form.is_valid():
            if form.cleaned_data['new_product']:
                if not form.fields['new_product'].initial:
                    form.instance.first_enabled = timezone.now()
            else:
                if form.instance.first_enabled:
                    form.instance.first_enabled = (timezone.now()
                                                   - timedelta(days=31))

            if (form.cleaned_data['enabled'] and
                    form.instance.first_enabled is None):
                form.instance.first_enabled = timezone.now()
            form.save()
            return redirect('product_view', gtin=detail.product.article.gtin)

    return render(
        request,
        'web/product_detail_edit.html',
        {
            'form': form
        })


@login_required
def product_tags_edit(request, gtin):
    product = Product.objects.get(article__gtin=gtin)
    selected_tags = product.tags.all()
    selected_tags_id_list = [str(t.id) for t in selected_tags]
    selected_tags_ids = ",".join(selected_tags_id_list)
    tags = Tag.objects.exclude(
        id__in=selected_tags_id_list).values_list('name', 'id')

    json_tags = json.dumps(list(tags))
    json_selected_tags = json.dumps(list(
        selected_tags.values_list('name', 'id')))

    form = TagsLinkForm()
    form['ids'].initial = selected_tags_ids

    if request.POST:
        tag_ids = request.POST.get('ids')

        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids.split(','))
            product.tags.set(tags)
        else:
            product.tags.clear()

        return redirect('product_view', gtin=gtin)

    return render(request, 'web/product_tags_edit.html',
                  {
                      'gtin': gtin,
                      'form': form,
                      'json_tags': json_tags,
                      'json_selected_tags': json_selected_tags,
                      'selected_tags': selected_tags,
                      'selected_tag_ids': selected_tags_ids
                  })


@login_required
def merchantarticle(request, id):
    merchantarticle = MerchantArticle.objects.get(pk=id)

    return render(request, 'web/merchantarticle.html',
                  {
                      'merchantarticle': merchantarticle
                  })


@login_required
def merchantarticle_search(request):
    form = MerchantArticleSearchForm(request.GET)
    pagesize = request.GET.get('pagesize', 10)
    parameters = request.GET.copy()

    merchantarticles = MerchantArticle.objects.all()

    if form.is_valid():
        merchantarticles = merchantarticles.filter(
            article_gtin__icontains=form.cleaned_data['gtin_input'],
            external_id__icontains=form.cleaned_data['external_id_input'],
            merchant_name__icontains=form.cleaned_data['merchant_name_input']
        )

        last_modified_start = form.cleaned_data[
            'last_modified_start_input']
        if last_modified_start is not None:
            merchantarticles = merchantarticles.filter(
                last_modified__gte=last_modified_start)

        last_modified_end = form.cleaned_data[
            'last_modified_end_input']
        if last_modified_end is not None:
            last_modified_end_datetime = datetime.combine(
                last_modified_end, datetime.max.time())
            merchantarticles = merchantarticles.filter(
                last_modified__lte=last_modified_end_datetime)

    paginator = Paginator(merchantarticles, pagesize)
    page = request.GET.get('page')
    pagelist = paginator.get_page(page)

    return render(request, 'web/merchantarticle_search.html',
                  {
                      'form': form,
                      'parameters': parameters,
                      'pagesize': int(pagesize),
                      'pagelist': pagelist,
                      'pagesizes': [10, 25, 50, 100, 250]
                  })


@login_required
def merchantarticle_add(request):
    form = MerchantArticleForm()

    if request.GET.get('gtin'):
        form.fields['article_gtin'].initial = request.GET.get('gtin')

    if request.method == 'POST':
        form = MerchantArticleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('merchantarticle_search')

    return render(request, 'web/merchantarticle_add.html',
                  {
                    'form': form
                  })


@login_required
def merchantarticle_edit(request, id):
    merchantarticle = MerchantArticle.objects.get(pk=id)
    form = MerchantArticleForm(instance=merchantarticle)

    if request.POST:
        saveform = MerchantArticleForm(request.POST, instance=merchantarticle)
        if saveform.is_valid():
            saveform.save()
            return redirect('merchantarticle_search')

    return render(request, 'web/merchantarticle_edit.html',
                  {
                      'merchantarticle': merchantarticle,
                      'form': form
                  })


@login_required
def tag(request, id):
    tag = Tag.objects.get(pk=id)

    return render(request, 'web/tag.html',
                  {
                      'tag': tag,
                  })


@login_required
def tag_search(request):
    form = TagSearchForm(request.GET)
    pagesize = request.GET.get('pagesize', 10)
    parameters = request.GET.copy()


    tags = Tag.objects.all()

    if form.is_valid():
        if form.cleaned_data['name']:
            tags = tags.filter(
                name__icontains=form.cleaned_data['name'])
        if form.cleaned_data['slug']:
            tags = tags.filter(
                slug__icontains=form.cleaned_data['slug'])

    paginator = Paginator(tags, pagesize)
    page = request.GET.get('page')
    pagelist = paginator.get_page(page)

    return render(request, 'web/tag_search.html',
                  {
                      'form': form,
                      'parameters': parameters,
                      'pagesize': int(pagesize),
                      'pagelist': pagelist,
                      'pagesizes': [10, 25, 50, 100, 250]
                  })


@login_required
def tag_add(request):
    form = TagForm()
    tags = list(Tag.objects.all().values_list('name', flat=True))

    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tag_search')

    return render(request, 'web/tag_add.html',
                  {
                    'tags': tags,
                    'form': form
                  })


@login_required
def tag_edit(request, id):
    tag = Tag.objects.get(pk=id)
    form = TagForm(instance=tag)

    if request.POST:
        saveform = TagForm(request.POST, instance=tag)
        if saveform.is_valid():
            saveform.save()
            return redirect('tag_search')

    return render(request, 'web/tag_edit.html',
                  {
                      'id': id,
                      'form': form
                  })


@login_required
def productcategory_search(request):
    form = ProductCategorySearchForm(request.GET)
    pagesize = request.GET.get('pagesize', 10)
    parameters = request.GET.copy()

    categories = ProductCategory.objects.all()

    if(form.is_valid()):
        categories = \
            categories.filter(
                name__icontains=form.
                cleaned_data
                ['category_name_input']
            )

        last_modified_start = form.cleaned_data[
            'last_modified_start_input']
        if last_modified_start is not None:
            categories = categories.filter(
                last_modified__gte=last_modified_start)

        last_modified_end = form.cleaned_data[
            'last_modified_end_input']
        if last_modified_end is not None:
            categories = categories.filter(
                last_modified__lte=last_modified_end)

    paginator = Paginator(categories, pagesize)
    page = request.GET.get('page')
    pagelist = paginator.get_page(page)

    return render(request, 'web/productcategory.html',
                  {
                      'form': form,
                      'parameters': parameters,
                      'pagesize': int(pagesize),
                      'pagelist': pagelist,
                      'pagesizes': [10, 25, 50, 100, 250]
                  })


@login_required
def productcategory_add(request):
    form = ProductCategoryForm()

    if request.method == 'POST':
        form = ProductCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('productcategory_search')

    return render(request, 'web/productcategory_add.html',
                  {
                      'form': form
                  })


@login_required
def productcategory_details(request, id):
    category = ProductCategory.objects.get(id=id)

    return render(request, 'web/productcategory_details.html',
                  {
                      'category': category
                  })


@login_required
def productcategory_edit(request, categoryid):
    category = ProductCategory.objects.get(id=categoryid)
    form = ProductCategoryForm(instance=category)

    if request.POST:
        saveform = ProductCategoryForm(request.POST, instance=category)
        if saveform.is_valid():
            saveform.save()
            return redirect('productcategory_search')

    return render(request, 'web/productcategory_edit.html',
                  {
                      'form': form,
                      'categoryid': categoryid
                  })


@login_required
def productcategory_tags_edit(request, id):
    category = ProductCategory.objects.get(id=id)

    selected_tags = category.tags.all()
    selected_tags_id_list = [str(t.id) for t in selected_tags]
    selected_tags_ids = ",".join(selected_tags_id_list)
    tags = Tag.objects.exclude(
        id__in=selected_tags_id_list).values_list('name', 'id')

    json_tags = json.dumps(list(tags))
    json_selected_tags = json.dumps(list(
        selected_tags.values_list('name', 'id')))

    form = TagsLinkForm()
    form['ids'].initial = selected_tags_ids

    if request.POST:
        tag_ids = request.POST.get('ids')

        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids.split(','))
            category.tags.set(tags)
        else:
            category.tags.clear()

        return redirect('productcategory_details', id=id)

    return render(request, 'web/productcategory_tags_edit.html',
                  {
                      'id': id,
                      'form': form,
                      'json_tags': json_tags,
                      'json_selected_tags': json_selected_tags,
                      'selected_tags': selected_tags,
                      'selected_tag_ids': selected_tags_ids
                  })
