appshell = {}

$(document).ready(function(){

    $('.dropdown-select').click(function(e) {
        if (!$(e.target).hasClass("custom-select-item")){
            e.stopPropagation();
        }
    }) ;

    
    $('.custom-select-item').click(function(e){
        var tgt = $(e.currentTarget);
        var cont = tgt.parents('.custom-select-container');
        var name = cont.data('custom-select-name');

        var value = tgt.data('value')
        var text = tgt.data('text')
        if (!text){
            text = tgt.text()
        }
        
        $("#"+name+"-text").text(text);
        $("#"+name).val(value)
        
        tgt.parents('.modal').modal('hide');
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
    });
        
        
    $('.checklist').each(function(i, e){
        var name = $(e).data('custom-select-name');
        function value_from_checks(){
            var value = ""
            var text = ""
            
            $(e).find('input[type="checkbox"]').each(function(i, c){
                if ($(c).prop('checked')){
                    value += $(c).val()+";";
                    if (text == ""){
                        text = $(c).parent().text();
                    } else {
                        text = "[..., ...]"
                    }
                }
            });
            

            $("#"+name+"-text").text(text);
            $("#"+name).val(value)
            $("#"+name).trigger('change');
        }
        function checks_from_value(){
            
        }
        console.log(e);
        $(e).find('input[type="checkbox"]').on("change", function f(){
            value_from_checks();
        });
    });

    $('.checktree').each(function(i, e){
        var name = $(e).data('custom-select-name');
        var changing = false;
        var tree = $(e);
        function value_from_checks(){
            var value = ""
            var text = ""
            $(e).find('input[type="checkbox"]').each(function(i, c){
                if ($(c).prop('checked')){
                    value += $(c).val()+";";
                    if (text == ""){
                        text = $(c).val();
                    } else {
                        text = "[..., ...]"
                    }
                }
            });
            
            $("#"+name+"-text").text(text);
            $("#"+name).val(value)
            $("#"+name).trigger('change');
        }
        function checks_from_value(){
            
        }
        $(e).find('input[type="checkbox"]').on("change", function f(e){
            var self = $(e.currentTarget);
            if (changing == false){
                changing = true;
                
                var checked = self.prop('checked');
                var myval = self.val()
                var desc = tree.find('input[type="checkbox"][value^="'+myval+'/"]')
                console.log(desc)
                desc.prop('checked', checked);
                console.log(checked);
                if (!checked){
                    var path = myval.split('/');
                    var i;
                    var s = path[0];
                    for (i = 1; i < (path.length); i++){
                        console.log(s)
                        tree.find("input[type='checkbox'][value='"+s+"']").prop('checked', false);
                        s = s + '/' + path[i];
                    }
                }
                
                changing = false;
                value_from_checks();
            }
        });
        
    });
    
    $('.datatable-action').click(function(e){
        var tgt = $(e.currentTarget);
        var id = tgt.data('target');
        var action = tgt.data('action');
        var t = appshell.datatables[id];

        paramstring = $.param(t.ajax.params());

        window.location = t.ajax.url() + '?action=' + action + '&' + paramstring;
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

