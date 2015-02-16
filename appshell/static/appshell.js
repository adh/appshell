$('.dropdown-select').click(function(e) {
          e.stopPropagation();
});


$('.dropdown-select-item').click(e){
    tgt = $(e.currentTarget);
    dd = tgt.parents('.dropdown-select')
    
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
}
