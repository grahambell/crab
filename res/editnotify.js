$(document).ready(function () {
    var notify_table = $('table#notifylist');
    var notifyrowtemplate = notify_table.data('row-template');

    var newRowNumber = 1;
    var timezones = null;

    var addTimezoneOptions = (function (select) {
        if (timezones !== null) {
            for (var i = 0; i < timezones.length; i ++) {
                var timezone = timezones[i];
                select.append($('<option/>', {'text': timezone, 'value': timezone}));
            }

            var selected = select.data('selected');
            if (selected !== '') {
                select.val(selected);
            }
        }
    });

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

        addTimezoneOptions($('select[name="timezone_' + nid + '"]'));

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

    $.ajax(notify_table.data('timezone-url'), {
        dataType: 'json',
    }).done(function (data) {
        timezones = data;

        $('select[name^="timezone_"]').each(function () {
            addTimezoneOptions($(this));
        });
    });
});
