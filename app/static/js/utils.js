$(document).ready(function() {
    $('a.js-csrf-submit').click(function() {
        var $emptyForm = $('#empty-form');
        $emptyForm.attr('action', $(this).attr('href'));
        $emptyForm.submit();
        return false;
    });
});

