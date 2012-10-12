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
        $('#table_' + crontab).show();
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
    $('#show_all_raw').click(function (event) {
        $('[id^="raw_"]').show();
        $('[id^="show_raw_"]').hide();
        $('[id^="hide_raw_"]').show();
        $('#show_all_raw').hide();
        $('#hide_all_raw').show();
        event.preventDefault();
    });
    $('#hide_all_raw').click(function (event) {
        $('[id^="raw_"]').hide();
        $('[id^="show_raw_"]').show();
        $('[id^="hide_raw_"]').hide();
        $('#show_all_raw').show();
        $('#hide_all_raw').hide();
        event.preventDefault();
    });
    $('#show_all_table').click(function (event) {
        $('[id^="table_"]').show();
        $('[class^="deleted_"]').hide();
        $('[id^="show_deleted_"]').show();
        $('[id^="hide_deleted_"]').hide();
        $('#show_all_table').hide();
        $('#hide_all_table').show();
        event.preventDefault();
    });
    $('#hide_all_table').click(function (event) {
        $('[id^="table_"]').hide();
        $('[id^="show_deleted_"]').show();
        $('[id^="hide_deleted_"]').hide();
        $('#show_all_table').show();
        $('#hide_all_table').hide();
        event.preventDefault();
    });
});
