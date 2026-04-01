$(document).ready(function () {
    var events_body = $('#jobevents');
    var events_form = $('#eventsform');

    var refresh_url = events_body.data('refresh-url');

    var refreshJobEvents = (function (enddate) {
        var params = events_form.serialize();

        if (enddate !== null) {
            params = params + '&enddate=' + encodeURIComponent(enddate);
        }

        $.ajax(refresh_url + '?barerows=1&' + params, {
            dataType: 'html',
            timeout: 10000
        }).done(function (data, text, xhr) {
            events_body.html(data);
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
        refreshJobEvents(lastDateTime);
        event.preventDefault();
    });
});
