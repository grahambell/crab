function refreshJobEventsSuccess(data, text, xhr) {
    $('#jobevents').html(data);
}

function refreshJobEventsError(xhr, text, error) {
    alert('Failed to retrieve events: ' + text);
}

function refreshJobEvents(enddate) {
    var params = $('#eventsform').serialize();

    if (enddate !== null) {
        params = params + '&enddate=' + encodeURIComponent(enddate);
    }

    $.ajax('/job/'+ jobidnumber + '?barerows=1&' + params, {
        dateType: 'html',
        success: refreshJobEventsSuccess,
        error: refreshJobEventsError,
        timeout: 10000
    });

    var stateObj = {'enddate': enddate};
    history.replaceState(stateObj, '', '/job/' + jobidnumber + '?' + params);
}

$(document).ready(function () {
    $('#eventsform').change(function (event) {
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
