$(document).ready(function () {
    var mainmenu = $('#mainmenu');
    $('#menubutton').click(function (event) {
        mainmenu.toggle();
        event.stopPropagation();
    });
    $(document).click(function (event) {
        if ($(event.target).parents('#mainmenu').length === 0) {
            mainmenu.hide();
        }
    });
});
