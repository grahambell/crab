$(document).ready(function () {
    var notify_table = $('table#notifylist');
    var notifyrowtemplate = notify_table.data('row-template');

    var newRowNumber = 1;

    var deleteRow = (function (notifyid) {
        var response = confirm(
            'Delete notification for '
            + $('#address_' + notifyid).val() + '?');
        if (response === true) {
            $('#row_' + notifyid).remove();
        }
    });

    $('#add_notification').click(function (event) {
        var nid = 'new_' + (newRowNumber ++);

        notify_table.append(notifyrowtemplate.replace(new RegExp('XXX', 'g'), nid));

        $('#delete_' + nid).click(function (event) {
            deleteRow(nid);
            event.preventDefault();
        });

        event.preventDefault();
    });

    $('[id^="delete_"]').click(function (event) {
        var nid = event.target.id.replace('delete_', '');

        deleteRow(nid);

        event.preventDefault();
    });
});
