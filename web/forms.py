from django import forms
from web.models import Article, Product, ProductDetail, ProductCategory, \
        Tag, MerchantArticle, Allergen


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        exclude = ['source', 'creation_date', 'last_modified', 'allergens']


class ArticleWhitelistForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ('whitelisted',)


class ArticleAllergensForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ('allergens',)
        widgets = {
            'allergens': forms.HiddenInput()
        }


class AllergenAddForm(forms.Form):
    containment_level = forms.ChoiceField(
        choices=list(Allergen.CONTAINMENT_LEVEL.items()))
    type_code = forms.ChoiceField(
        choices=list(Allergen.TYPE.items()), label='Type')


class ArticleSearchForm(forms.Form):
    gtin_input = forms.CharField(label='GTIN', max_length=100, required=False)
    name_input = forms.CharField(label='Product Name', required=False)
    category_input = forms.CharField(label='Category', required=False)
    brand_name_input = forms.CharField(label='Brand Name', required=False)
    source = forms.CharField(label='Data Source', required=False)
    last_modified_start_input = forms.DateField(
        label='Last Modified Start', required=False,
        widget=forms.TextInput(attrs={'class': 'datepicker'}))
    last_modified_end_input = forms.DateField(
        label='Last Modified End', required=False,
        widget=forms.TextInput(attrs={'class': 'datepicker'}))
    only_complete = forms.BooleanField(
        label='Only show complete articles', required=False)
    include_packages = forms.BooleanField(
        label='Include packages', required=False)


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['article', 'tags', 'allergens']


class ProductDetailForm(forms.ModelForm):
    new_product = forms.BooleanField(
        label="Tagged as new product", required=False)

    class Meta:
        model = ProductDetail
        exclude = ['first_enabled','article', 'store', 'product']


class ProductImageAddForm(forms.Form):
    filename = forms.CharField(widget=forms.ClearableFileInput, required=True)
    active = forms.BooleanField(required=False)


class ProductImportCSVForm(forms.Form):
    filename = forms.CharField(widget=forms.ClearableFileInput, required=True)
    update_if_exists = forms.BooleanField(required=False)


class ProductSearchForm(forms.Form):
    product_id_input = forms.CharField(
        label='ProductID', max_length=100, required=False)
    gtin_input = forms.CharField(label='GTIN', max_length=100, required=False)
    product_name_input = forms.CharField(label='Product Name', required=False)
    brand_name_input = forms.CharField(label='Brand Name', required=False)
    source = forms.CharField(label='Data Source', required=False)
    tags = forms.CharField(label='Tag', required=False)
    last_modified_start_input = forms.DateField(
        label='Last Modified Start', required=False,
        widget=forms.TextInput(attrs={'class': 'datepicker'}))
    last_modified_end_input = forms.DateField(
        label='Last Modified End', required=False,
        widget=forms.TextInput(attrs={'class': 'datepicker'}))


class IncompleteProductSearchForm(ProductSearchForm):
    include_invalid_image = forms.BooleanField(
        label='Include invalid image', required=False, initial=True)
    include_invalid_brand = forms.BooleanField(
        label='Include invalid brand', required=False, initial=True)
    include_invalid_price = forms.BooleanField(
        label='Include invalid price', required=False, initial=True)
    include_invalid_vat = forms.BooleanField(
        label='Include invalid VAT', required=False, initial=True)
    include_invalid_weight = forms.BooleanField(
        label='Include invalid weight', required=False, initial=True)
    include_invalid_volume = forms.BooleanField(
        label='Include invalid volume', required=False, initial=True)


class ProductRecentChangesForm(forms.Form):
    TYPES = (
        ('All', 'All'),
        ('+', 'Created'),
        ('~', 'Changed'),
        ('-', 'Deleted'),
    )
    gtin = forms.CharField(label='GTIN', max_length=100, required=False)
    product_name = forms.CharField(label='Product Name', required=False)
    changed_type = forms.ChoiceField(
        label='Type', required=False, choices=TYPES)
    changed_by = forms.CharField(label='Changed By', required=False)


class ProductAllergensForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('allergens',)
        widgets = {
            'allergens': forms.HiddenInput()
        }


class MerchantArticleForm(forms.ModelForm):
    class Meta:
        model = MerchantArticle
        exclude = ('article', 'listed', 'last_date_to_order',)


class MerchantArticleSearchForm(forms.Form):
    gtin_input = forms.CharField(label='GTIN', max_length=100, required=False)
    merchant_name_input = forms.CharField(label='Merchant Name',
                                          required=False)
    external_id_input = forms.CharField(label='External Id', required=False)
    last_modified_start_input = forms.DateField(
        label='Last Modified Start', required=False,
        widget=forms.TextInput(attrs={'class': 'datepicker'}))
    last_modified_end_input = forms.DateField(
        label='Last Modified End', required=False,
        widget=forms.TextInput(attrs={'class': 'datepicker'}))


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = '__all__'


class TagSearchForm(forms.Form):
    name = forms.CharField(label='Name', required=False)
    slug = forms.CharField(label='Slug', required=False)


class TagsLinkForm(forms.Form):
    ids = forms.CharField(widget=forms.HiddenInput(), required=False)


class ProductCategorySearchForm(forms.Form):
    category_name_input = forms.CharField(
        label='Category Name', required=False)
    last_modified_start_input = forms.DateField(
        label='Last Modified Start', required=False,
        widget=forms.TextInput(attrs={'class': 'datepicker'}))
    last_modified_end_input = forms.DateField(
        label='Last Modified End', required=False,
        widget=forms.TextInput(attrs={'class': 'datepicker'}))


class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        exclude = ('removed_date', 'creation_date', 'last_modified', 'tags')
