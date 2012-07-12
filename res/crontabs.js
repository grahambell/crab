$(document).ready(function () {
    $('[id^="show_raw_"]').click(function (event) {
        var crontab = event.target.id.replace('show_raw_', '');
        $('#raw_' + crontab).show();
        $('#show_raw_' + crontab).hide();
        $('#hide_raw_' + crontab).show();
        event.preventDefault();
    });
    $('[id^="hide_raw_"]').click(function (event) {
        var crontab = event.target.id.replace('hide_raw_', '');
        $('#raw_' + crontab).hide();
        $('#show_raw_' + crontab).show();
        $('#hide_raw_' + crontab).hide();
        event.preventDefault();
    });
    $('[id^="show_deleted_"]').click(function (event) {
        var crontab = event.target.id.replace('show_deleted_', '');
        $('.deleted_' + crontab).show();
        $('#show_deleted_' + crontab).hide();
        $('#hide_deleted_' + crontab).show();
        event.preventDefault();
    });
    $('[id^="hide_deleted_"]').click(function (event) {
        var crontab = event.target.id.replace('hide_deleted_', '');
        $('.deleted_' + crontab).hide();
        $('#show_deleted_' + crontab).show();
        $('#hide_deleted_' + crontab).hide();
        event.preventDefault();
    });
});
