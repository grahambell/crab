var newRowNumber = 1;

function addRow() {
    var nid = 'new_' + (newRowNumber ++);
    $('table#notifylist').append(notifyrowtemplate.replace(new RegExp('XXX', 'g'), nid));
    $('#delete_' + nid).click(function (event) {
        deleteRow(nid);
        event.preventDefault();
    });
}

function deleteRow(notifyid) {
    var response = confirm('Delete notification for ' +
                           $('#address_' + notifyid).val() + '?')
    if (response === true) {
        $('#row_' + notifyid).remove();
    }
}

$(document).ready(function () {
    $('#add_notification').click(function (event) {
        addRow();
        event.preventDefault();
    });

    $('[id^="delete_"]').click(function (event) {
        var notifyid = event.target.id.replace('delete_', '');
        deleteRow(notifyid);
        event.preventDefault();
    });
});
