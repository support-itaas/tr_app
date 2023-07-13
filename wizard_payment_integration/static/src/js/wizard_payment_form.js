$(document).ready(function() {

$('#cardNumber').on('keyup', function(e){
console.log("hsgshgd");
    var val = $(this).val();
    var newval = '';
    val = val.replace(/\s/g, '');
    for(var i=0; i < val.length; i++) {
        if(i%4 == 0 && i > 0) newval = newval.concat(' ');
        newval = newval.concat(val[i]);
    }
    $(this).val(newval);
});

$('#cardNumber').on('change', function(e){
var cardNumber = $('#cardNumber').val();
if(cardNumber.length != 19){
$('#card_validation_warning').show();
}
else{
$('#card_validation_warning').hide();
}
});

$('#cvv').on('change', function(e){
var cvv = $('#cvv').val();
console.log(cvv)
if(cvv.length !=4){
$('#warning').show();
}
else{
$('#warning').hide();
}
});
});

