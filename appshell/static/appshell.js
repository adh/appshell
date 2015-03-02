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

    if (t.column(column).search() != value){
        t.column(column).search(value).draw();
    }
})


$('.tablefilter-range').each(function(i, elem){
    var eq =$(elem);
    var id = eq.data('tablefilter-target');
    var column = eq.data('tablefilter-column');
    function update(e){
        var t = appshell.datatables[id]; 
        var value = eq.find('.range-from').val() + ';' + eq.find('.range-to').val();        
        if (t.column(column).search() != value){
            t.column(column).search(value).draw();
        }
    }
    eq.find('.range-from').on('keyup change', update);
    eq.find('.range-to').on('keyup change', update);
})


$('.checklist').each(function(i, e){
    var name = $(e).data('dropdown-select-name')
    function value_from_checks(){
        var value = ""
        var text = ""
        
        $(e).find('input[type="checkbox"]').each(function(i, c){
            if ($(c).prop('checked')){
                value += $(c).val()+";";
                text += $(c).parent().text()+", ";
            }
        });

        $("#"+name+"-text").text(text);
        $("#"+name).val(value)
    }
    function checks_from_value(){
        
    }
    console.log(e);
    $(e).find('input[type="checkbox"]').on("change", function f(){
        value_from_checks();
    });
});

(function(){
    var timeout;
    $(document).ajaxStart(function(){
        timeout = setTimeout("$('.appshell-spinner').show()", 200);
    });
    $(document).ajaxStop(function(){
        if (timeout){
            clearTimeout(timeout);
        }
        timeout = null;
        $('#appshell-ajax-spinner').hide();
    });
})()
