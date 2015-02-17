appshell = {}

$('.dropdown-select').click(function(e) {
          e.stopPropagation();
});


$('.dropdown-select-item').click(function(e){
    var tgt = $(e.currentTarget);
    var dd = tgt.parents('.dropdown-select')
    
    if (dd.data('value-target')){
        value = tgt.data('value')
        $(dd.data('value-target')).val(value)
    }
    if (dd.data('text-target')){
        text = tgt.data('text')
        if (!text){
            text = tgt.text()
        }
        $(dd.data('text-target')).text(text)
    }
});

appshell.datatables = {}

$('.tablefilter').on('keyup change', function (e){
    var tgt = $(e.currentTarget);
    var id = tgt.data('tablefilter-target');
    var t = appshell.datatables[id];
    

    var column = tgt.data('tablefilter-column');
    var value = tgt.val()

    t.columns(column).search(value).draw();
})
