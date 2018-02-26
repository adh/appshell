appshell = {}

$(document).ready(function(){

    $('.dropdown-select').click(function(e) {
        if (!$(e.target).hasClass("custom-select-item")){
            e.stopPropagation();
        }
    }) ;

    $('.checklist-select-all').click(function(e) {
	$(e.target).parent().find('input').prop('checked', true);
	$(e.target).parent().find('input').first().trigger('change');
    }) ;
    $('.checklist-deselect-all').click(function(e) {
	$(e.target).parent().find('input').prop('checked', false);
	$(e.target).parent().find('input').first().trigger('change');
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

    function table_clear_timeout(t){
        if ('appshell_timeout' in t){
	    clearTimeout(t.appshell_timeout);
	}
    }
    
    function table_apply_filter(t, tgt){
        var column = tgt.data('tablefilter-column');
        var value = tgt.val()

	table_clear_timeout(t);
	
        if (t.column(column).search() != value){
            t.column(column).search(value).draw();
        }
    }

    function table_start_timeout(t, tgt){
	var timeout = tgt.data('tablefilter-timeout');
	if (!timeout){
            timeout = 500;
	}
	table_clear_timeout(t);
	setTimeout(function(){
	    table_apply_filter(t, tgt);
	}, timeout);
    }
    
    $('.tablefilter').on('change', function (e){
        var tgt = $(e.currentTarget);
        var id = tgt.data('tablefilter-target');
        var t = appshell.datatables[id];
        
        table_apply_filter(t, tgt);
    });

    $('.tablefilter').on('keyup', function (e){
        var tgt = $(e.currentTarget);
        var id = tgt.data('tablefilter-target');
        var t = appshell.datatables[id];

	var minlength = tgt.data('tablefilter-min-length');
	if (minlength){
	    var len = tgt.val().length;
	    if ((len > 0) && (len < minlength)){
		return;
	    }
	}
	
	if (e.which == 13){
            table_apply_filter(t, tgt);
	} else {
            table_start_timeout(t, tgt);
	}
    });
    
    
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
        function value_from_checks(trig){
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
            $("#"+name).val(value);
            if (trig){
                $("#"+name).trigger('change');
            }
        }
        function checks_from_value(){
            var val = $("#"+name).val();
            var list = val.split(";")
            console.log(list);
            $(e).find('input[type="checkbox"]').each(function(i, c){
                var value = $(c).val();
                console.log(value);
                console.log(value in list);
                if (list.indexOf(value) != -1){
                    $(c).prop('checked', true);
                }
            });
            
        }
        checks_from_value();
        value_from_checks(false);
        console.log(e);
        $(e).find('input[type="checkbox"]').on("change", function f(){
            value_from_checks(true);
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

    $('.bootstrap-markdown').markdown({"autofocus": false});

    $('.datatable-action').click(function(e){
        var tgt = $(e.currentTarget);
        var id = tgt.data('target');
        var action = tgt.data('action');
        var t = appshell.datatables[id];
        var url = t.ajax.url();
        var paramstring = $.param(t.ajax.params());
        var new_window = tgt.data('new-window');
        
        var action_url = (url + 
                           ((url.indexOf('?') == -1) ? '?' : '&') + 
                           'action=' + action + 
                          '&' + paramstring);

        if (new_window){
            window.open(action_url);
        } else {
            window.location = action_url;
        }
    });

    function treegrid_expand_all(tgt){
        var sts = tgt.treegrid('getTreeContainer').data('settings');
        if (sts.appshellDisabledState){
            return;
        }
        sts.appshellDisabledState = true;
        tgt.treegrid('saveState');
        sts.saveState = false;
        tgt.treegrid('expandAll');
    }

    function treegrid_restore(tgt){
        var sts = tgt.treegrid('getTreeContainer').data('settings');
        if (sts.appshellDisabledState){
            tgt.treegrid('getAllNodes').each(function(idx, i){
                $(i).css('display', 'table-row');
            });

            sts.appshellDisabledState = false;
            sts.saveState = true;
            tgt.treegrid('getAllNodes').each(function(idx, i){
                $(i).treegrid('restoreState');
            });
        }
    }

    $('.treegrid-search').on('keyup change', function(e){
        var myself = $(e.currentTarget);
        var tgt = $(myself.data('target'));
        var str = myself.val().toLowerCase()
        if (str != ""){
            treegrid_expand_all(tgt);
            tgt.treegrid('getAllNodes').each(function(idx, i){
                var self = $(i);
                if (self.text().toLowerCase().indexOf(str) != -1){
                    self.css('display', 'table-row');
                } else {
                    self.css('display', 'none');
                }
            });
        } else {
            treegrid_restore(tgt);            
        }
    });

    $('select[multiple]').selectpicker({"selectedTextFormat": "count > 3"});
    $('select[data-search]').selectpicker({"liveSearch": true,
					   "liveSearchNormalize": true});
    
});

(function(){
    var timeout;
    $(document).ajaxStart(function(){
        timeout = setTimeout("$('.appshell-spinner').show()", 50);
    });
    $(document).ajaxStop(function(){
        if (timeout){
            clearTimeout(timeout);
        }
        timeout = null;
        $('#appshell-ajax-spinner').hide();
    });
})()

/* file-size plugin */
jQuery.fn.dataTable.ext.type.detect.unshift( function ( data ) {
    if ( typeof data !== 'string' ) {
        return null;
    }
 
    var units = data.replace( /[\d\.]/g, '' ).toLowerCase();
    if ( units !== '' && units !== 'b' && units !== 'kb' && units !== 'mb' && units !== 'gb' ) {
        return null;
    }
 
    return isNaN( parseFloat( data ) ) ?
        null :
        'file-size';
} );
jQuery.fn.dataTable.ext.type.order['file-size-pre'] = function ( data ) {
    var units = data.replace( /[\d\.]/g, '' ).toLowerCase();
    var multiplier = 1;
 
    if ( units === 'kb' ) {
        multiplier = 1000;
    }
    else if ( units === 'mb' ) {
        multiplier = 1000000;
    }
    else if ( units === 'gb' ) {
        multiplier = 1000000000;
    }
 
    return parseFloat( data ) * multiplier;
};
