$(document).ready(function () {
    var events_table = $('#jobevents');
    var events_form = $('#eventsform');

    var refresh_url = events_table.data('refresh-url');

    var refreshJobEvents = (function (enddate) {
        var params = events_form.serialize();

        if (enddate !== null) {
            params = params + '&enddate=' + encodeURIComponent(enddate);
        }

        $.ajax(refresh_url + '?barerows=1&' + params, {
            dataType: 'html',
            timeout: 10000
        }).done(function (data, text, xhr) {
            events_table.find('tbody').remove();
            events_table.append(data);
        }).fail(function (xhr, text, error) {
            alert('Failed to retrieve events: ' + text);
        });

        var stateObj = {'enddate': enddate};
        history.replaceState(stateObj, '', refresh_url + '?' + params);
    });

    events_form.change(function (event) {
        if (history.state && ('enddate' in history.state)) {
            refreshJobEvents(history.state.enddate);
        }
        else {
            refreshJobEvents(null);
        }
    });

    $('#eventslast').click(function (event) {
        refreshJobEvents(null);
        event.preventDefault();
    });

    $('#eventsprev').click(function (event) {
        var lastDateTime = events_table.find('tbody').data('last-datetime');
        refreshJobEvents(lastDateTime);
        event.preventDefault();
    });
});
