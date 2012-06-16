function updateStatusBox(id, status_, running) {
    var box = $('#status_' + id);
    switch (status_) {
        case 0:
            box.text('Succeeded');
            box.removeClass().addClass('status_ok');
            break;
        case 1:
            box.text('Failed');
            box.removeClass().addClass('status_fail');
            break;
        case 2:
            box.text('Unknown');
            box.removeClass().addClass('status_warn');
            break;
        case 3:
            box.text('Could not start');
            box.removeClass().addClass('status_fail');
            break;
        case -1:
            box.text('Late');
            box.removeClass().addClass('status_ok');
            break;
        case -2:
            box.text('Missed');
            box.removeClass().addClass('status_warn');
            break;
        case -3:
            box.text('Timed out');
            box.removeClass().addClass('status_fail');
            break;
        case null:
            box.text('Unknown');
            box.removeClass().addClass('status_unknown');
            break;
        default:
            box.text('Status ' + status_);
            box.removeClass().addClass('status_warn');
    }
    if (running) {
        box.addClass('status_running');
    }
}


function updateReliabilityBox(id, reliability) {
    var box = $('#reliability_' + id);
    if (reliability > 100) {
        reliability = 100;
    }
    if (reliability < 0) {
        reliability = 0;
    }
    box.attr('title', 'Success rate: ' + reliability + '%');
    var stars = '';
    while (reliability >= 20) {
        stars = stars.concat('&#x2605');
        reliability -= 20;
    }
    if (reliability >= 10) {
        stars = stars.concat('&#x2606');
    }
    box.html(stars);
    box.removeClass().addClass('status_normal');
}

function updateInfo(data) {
    var id = data['id'];
    $('#host_' + id).text(data['host']);
    $('#user_' + id).text(data['user']);
    $('#command_' + id).text(data['command']);
    if (data['jobid'] !== null) {
        $('#jobid_' + id).text(data['jobid']);
        $('#jobid_' + id).removeClass();
    }
}

function setFavicon(url) {
    var favicon = $('link[rel=icon]');
    favicon.replaceWith(favicon.clone().attr('href', url));
}

function updateStatus(data) {
    var statusdata = data['status'];
    for (var id in statusdata) {
        var job = statusdata[id];

        if ($('#row_'+id).length == 0) {
            $('table#joblist').append(joblistrowtemplate.replace('XXX', id, 'g'));
            $.ajax('/query/jobinfo/' + id, {
                dataType: 'json',
                success: updateInfo
            });
        }

        updateStatusBox(id, job['status'], job['running']);
        updateReliabilityBox(id, job['reliability']);
    }

    var current_time = new Date();
    $('#last_refresh').text(current_time.toString());

    if (data['numerror'] > 0) {
        setFavicon('/res/favicon-error.png');
    }
    else if (data['numwarning'] > 0) {
        setFavicon('/res/favicon-warn.png');
    }
    else {
        setFavicon('/res/favicon.png');
    }
}

function refreshStatusOnceSuccess(data, text, xhr) {
    updateStatus(data);
}

function refreshStatusOnceError(xhr, text, error) {
    $('#last_refresh').text('Failed to fetch status from server.');
}

function refreshStatusOnce() {
    $.ajax('/query/jobstatuscomet?startid=0&warnid=0&finishid=0', {
        dataType: 'json',
        success: refreshStatusOnceSuccess,
        error: refreshStatusOnceError,
    });
}

function refreshStatusCometSuccess(data, text, xhr) {
    updateStatus(data);
    refreshStatusCometLoop(data['startid'], data['warnid'], data['finishid']);
}

function refreshStatusCometResume() {
    refreshStatusCometLoop(0, 0, 0);
    $('table#joblist').fadeTo(500, 1.0);
}

function refreshStatusCometError(xhr, text, error) {
    setTimeout(refreshStatusCometResume, 600000);
    $('table#joblist').fadeTo(500, 0.3);
    setFavicon(disconnectFavicon);
}

function refreshStatusCometLoop(startid, warnid, finishid) {
    $.ajax('/query/jobstatuscomet?startid=' + startid + '&warnid=' + warnid + '&finishid=' + finishid, {
        dataType: 'json',
        success: refreshStatusCometSuccess,
        error: refreshStatusCometError,
        timeout: 150000
    });
}


$(document).ready(function () {
    refreshStatusCometLoop(0, 0, 0);

    $('#command_refresh').click(function (event) {
        refreshStatusOnce();
        event.preventDefault();
    });

    // Need to load the disconnected icon now because if the
    // server vanishes we will not be able to load it when
    // needed.
    image = new Image();
    image.onload = function () {
        var canvas = document.createElement('canvas');
        canvas.width = 16;
        canvas.height = 16;
        context = canvas.getContext('2d');
        context.drawImage(image, 0, 0);
        disconnectFavicon = canvas.toDataURL('image/png');
    };
    image.src = '/res/favicon-disconnect.png'
});
