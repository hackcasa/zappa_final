$(document).ready(function () {

    $("#select_all").change(function () {
        $(".checkbox").prop('checked', $(this).prop("checked"));
    });

    $('.checkbox').change(function () {
        if (false == $(this).prop("checked")) {
            $("#select_all").prop('checked', false);
        }
        if ($('.checkbox:checked').length == $('.checkbox').length) {
            $("#select_all").prop('checked', true);
        }
    });

    $('.image-zoom').each(function () {
        element = $(this).find('img').get(0)
        zoomImage = $(this).find('img').attr('zoom')
        $(element).tooltip({
            container: this,
            title: '<img class="static-image-size-large" src="' + zoomImage + '">',
            html: true
        });

    });

    $('.datepicker').datepicker({
        dateFormat: "yy-mm-dd",
        changeMonth: true,
        changeYear: true
    });
    $('.datepicker').attr("autocomplete", "off");

    $('.article-edit-form').each(function () {
        $form = $(this)

        $('select[name="descriptor_code"]', $form).change(function () {
            var selected = $('option:selected', $(this)).text();

            if (selected == 'BASE_UNIT_OR_EACH') {
                $('#id_quantity_of_lower_layer', $form).parents('tr').fadeTo('fast', 0.3)
                $('#id_child_gtin', $form).parents('tr').fadeTo('fast', 0.3)
            } else {
                $('#id_quantity_of_lower_layer', $form).parents('tr').fadeTo('fast', 1)
                $('#id_child_gtin', $form).parents('tr').fadeTo('fast', 1)
            }
        });
        $('select[name="descriptor_code"]', $form).change()
    });

    if (window.location.hash) {
        if (window.location.hash.indexOf("new-article-") !== -1) {
            var parts = window.location.hash.split('-');

            if (parts.length == 3 && /^([0-9]{14})$/.test(parts[2])) {
                $.toast({
                    heading: 'Article Created!',
                    text: '<a href="/merchantarticle/add/?gtin=' + parts[2] + '" style="border-bottom: 0px;">To make the article orderable you need at least one MerchantArticle. Click here to create one</a>',
                    icon: 'success',
                    loader: false,
                    hideAfter: 10000,
                    position: 'top-right'
                })

                window.location.hash = ''
            }
        }
    }

    if (typeof (tags_list) == 'object') {
        var options = {
            shouldSort: true,
            threshold: 0.2,
            location: 0,
            distance: 100,
            maxPatternLength: 32,
            minMatchCharLength: 1
        };
        var fuse = new Fuse(tags_list, options);

        $('input[name="name"]').keyup(function () {
            var query = $(this).val();
            var result = fuse.search(query);
            var topResults = result.slice(0, 10);
            if (topResults.length > 0) {
                $('.tag-list-results li').remove();

                var append = ""
                topResults.forEach(result => {
                    append += ('<li class="list-group-item">' + tags_list[result] + '</li>');
                });

                $('.tag-list-results').append(append);
                $('.tag-list-search').removeClass('d-none');
            } else {
                $('.tag-list-search').addClass('d-none');
            }
        });
    }

    $('.form-copy-default').click(function () {
        var $target = $($(this).attr('data-target'));

        if ($target.val() == '' || confirm("The target field is not empty, do you want to override it?")) {
            var $source = $($(this).attr('data-source'));

            $target.val($source.text().trim());
        }
    });

    /* Tag edit for Product and ProductCategory */
    if (typeof (availableTagsList) == 'object') {
        availableTagsList = availableTagsList.map(t => { return { id: t[1], name: t[0] } });
        selectedTagsList = selectedTagsList.map(t => { return { id: t[1], name: t[0] } });

        /* Init FuseJS */
        var options = {
            shouldSort: true,
            threshold: 0.2,
            location: 0,
            distance: 100,
            maxPatternLength: 32,
            minMatchCharLength: 1,
            keys: ['name']
        };
        var fuse = new Fuse(availableTagsList, options);

        /* Tag filter handler */
        $('.tags-filter').keyup(function () {
            var query = $(this).val();
            var fuseResult = fuse.search(query);
            var topResults = fuseResult.slice(0, 20);
            if (topResults.length > 0) {
                var searchTagsHtml = ''
                topResults.forEach(element => {
                    searchTagsHtml += '<span class="p-1 d-inline-block mr-2 mb-2 btn rounded border border-secondary clickable-tag available" data-tag-id="' + element.id + '">' + element.name + '</span>'
                });
                $('.tags.available').html(searchTagsHtml);
            }
        });

        /* Set initial tags to show */
        var initialTags = availableTagsList.slice(0, 20)
        var initialTagsHtml = ''
        initialTags.forEach(element => {
            initialTagsHtml += '<span class="p-1 d-inline-block mr-2 mb-2 btn rounded border border-secondary clickable-tag available" data-tag-id="' + element.id + '">' + element.name + '</span>'
        });


        /* Tag click handler */
        $('.tags').on('click', '.clickable-tag', function () {
            let id = $(this).attr('data-tag-id');

            /* Update selected tags */
            if ($(this).hasClass('available')) {
                availableTagsList.forEach((element, index) => {
                    if (element.id == id) {
                        let tag = availableTagsList.splice(index, 1);
                        selectedTagsList = selectedTagsList.concat(tag);
                    }
                });
            } else {
                selectedTagsList.forEach((element, index) => {
                    if (element.id == id) {
                        let tag = selectedTagsList.splice(index, 1);
                        availableTagsList = availableTagsList.concat(tag);
                    }
                });
            }

            /* Set selected tags */
            let selectedTagsHtml = '';
            selectedTagsList.forEach(element => {
                selectedTagsHtml += '<span class="p-1 d-inline-block mr-2 mb-2 btn rounded border border-info bg-info text-white clickable-tag selected" data-tag-id="' + element.id + '">' + element.name + '</span>'
            });

            $('.tags.selected').html(selectedTagsHtml);
            let selectedIds = selectedTagsList.map(t => t.id);
            $('input[name="ids"]').val(selectedIds.join(','));

            $(this).remove();

            /* Reset FuseJS */
            fuse = new Fuse(availableTagsList, options);
        });

        /* Set initial, remove loader, enable save button */
        $('.tags.available').html(initialTagsHtml)
        $('.tags-loader').remove()
        $('.tags-save').prop('disabled', false)
    }

    $('.btn.add-allergen').click(function (e) {
        e.preventDefault();

        let containmentLevel = $('select[name="containment_level"]').val().trim();
        let typeCode = $('select[name="type_code"]').val().trim();
        let currentAllergens = JSON.parse($('#id_allergens').val());

        if ($.isEmptyObject(currentAllergens)) {
            currentAllergens = [];
        }

        /* Check if it's already set */
        if (currentAllergens.some(function (allergen) {
            return allergen.type_code == typeCode && allergen.containment_level_code == containmentLevel
        })) {
            return;
        }

        currentAllergens.push({
            'type_code': typeCode,
            'containment_level_code': containmentLevel
        })

        $('#id_allergens').val(JSON.stringify(currentAllergens));

        updateAllergenList();
    });

    $('.allergens-edit.set').on('click', '.remove-allergen', function (e) {
        e.preventDefault();

        let currentAllergens = JSON.parse($('#id_allergens').val());
        let containmentLevel = $(this).attr('data-containment-level');
        let typeCode = $(this).attr('data-type-code');
        let newAllergens = currentAllergens.filter(allergen => !(allergen.type_code == typeCode && allergen.containment_level_code == containmentLevel))

        $('#id_allergens').val(JSON.stringify(newAllergens));

        updateAllergenList();
    });

    $('.article-import-checkbox').change(function() {
        $('#import-selected-button').prop(
            'disabled',
            $('.article-import-checkbox:checked').length == 0
        );
    });
});


function updateAllergenList() {
    let currentAllergens = JSON.parse($('#id_allergens').val());

    /* Create new HTML list */
    let allergenHtml = ''
    currentAllergens.forEach(allergen => {
        allergenHtml += '<li class="list-group-item  d-flex justify-content-between">' +
            $('select[name="containment_level"] option[value="' + allergen.containment_level_code + '"]').text() + ' ' +
            $('select[name="type_code"] option[value="' + allergen.type_code + '"]').text() +
            '<a href="" class="remove-allergen" data-type-code="' + allergen.type_code + '" data-containment-level="' + allergen.containment_level_code + '">Remove</a>';
    });
    $('.allergens-edit.set .allergen-list').html(allergenHtml);

}