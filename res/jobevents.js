function refreshJobEventsSuccess(data, text, xhr) {
    $('#jobevents').html(data);
}

function refreshJobEventsError(xhr, text, error) {
    alert('Failed to retrieve events: ' + text);
}

function refreshJobEvents(enddate) {
    var params = '?barerows=1&' + $('#eventsform').serialize();

    if (enddate !== null) {
        params = params + '&enddate=' + encodeURIComponent(enddate);
    }

    $.ajax('/job/'+ jobidnumber + params, {
        dateType: 'html',
        success: refreshJobEventsSuccess,
        error: refreshJobEventsError,
        timeout: 10000
    });
}

$(document).ready(function () {
    $('#eventsform').change(function (event) {
        refreshJobEvents(null);
    });

    $('#eventsback').click(function (event) {
        refreshJobEvents(null);
        event.preventDefault();
    });

    $('#eventsnext').click(function (event) {
        refreshJobEvents(lastDateTime);
        event.preventDefault();
    });
});
