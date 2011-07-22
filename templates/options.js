function webreq(uri, method, successFn, errorFn) {
    //console.log('webreq');
    $.ajax({url: uri,
             type: method,
             success: successFn,
             error: errorFn });
}
 
function autocompleteItems(text) {
    //console.log('autocompleteItems');
    var res = jQuery.parseJSON(text);
    var arr = [];
    $.each(res.ResultSet.Result,
            function(i, v) {
                var obj = {};
                obj.label = v.symbol + ' : ' + v.name;
                obj.value = v.symbol;
                arr.push(obj);
            });
    return arr;
}
function selectStock(event, ui) {
    $('[name=goButton]').html('<img src="http://localhost/stock/loader.gif" />');
    webreq('/stock/' + $('[name=ticker]').val(), 'GET',
            function(text, stat, xhr) {
                //console.log(text);
                var res = text;
                $('[name=price]').html(res.last);
                $('[name=volume]').html(res.volume);
                $('[name=high]').html(res.high);
                $('[name=low]').html(res.low);
                $('[name=goButton]').html('Go!');
            }, null);
    webreq('/optionchain/' + $('[name=ticker]').val(), 'GET',
            function(text, stat, xhr) {
                var res = text;
                //console.log(res);
                $('[name=strips]').children().remove();
                $('[name=expiry]').children().remove();
                $.each(res.expirations,
                        function(i,v) {
                            var dateVal = String(v.m) + String(v.d) + String(v.y);
                            var dateStr = v.m + '/' + v.d + '/' + v.y;
                            //console.log(dateVal + dateStr);
                            $('<option value="'+dateVal+'">'+dateStr+'</option>').appendTo($('[name=expiry]'));
                            });
                $.each(res.calls,
                        function(i,v) {
                            var strike = v.strike;
                            var lastCallPrice = v.p;
                            var callBid = v.b;
                            var callAsk = v.a;
                            var callChange = v.c;
                            var callVolume = v.vol;
                            var lastPutPrice = res.puts[i].p;
                            var putBid = res.puts[i].b;
                            var putAsk = res.puts[i].a;
                            var putChange = res.puts[i].c;
                            var putVolume = res.puts[i].vol;
                            var strip = $('<tr></tr>');
                            $('<td>'+lastCallPrice+'</td>').appendTo(strip);
                            $('<td>'+callBid+'</td>').appendTo(strip);
                            $('<td>'+callAsk+'</td>').appendTo(strip);
                            $('<td>'+strike+'</td>').appendTo(strip);
                            $('<td>'+lastPutPrice+'</td>').appendTo(strip);
                            $('<td>'+putBid+'</td>').appendTo(strip);
                            $('<td>'+putAsk+'</td>').appendTo(strip);
                            strip.appendTo($('[name=strips]'));
                        });
 
                }, null);
}
 
$(document).ready(
    function() {
        $('[name=ticker]').autocomplete({
            delay: 250,
            select: selectStock,
            source:
                function(req, add) {
                    webreq('/search/' + req.term, 'GET', 
                        function(text, stat, xhr) {
                            add(autocompleteItems(text));
                            }, null);
                        }
            });
     });
