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
    box = $('#reliability_' + id)
    if (reliability > 100) {
        reliability = 100;
    }
    if (reliability < 0) {
        reliability = 0;
    }
    box.attr('title', 'Success rate: ' + reliability + '%');
    var stars = ''
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
    id = data['id']
    $('#host_' + id).text(data['host']);
    $('#user_' + id).text(data['user']);
    $('#command_' + id).text(data['command']);
    if (data['jobid'] !== null) {
        $('#jobid_' + id).text(data['jobid']);
    }
}

function updateStatus(data) {
    for (var id in data) {
        var job = data[id];

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
}

function refreshStatus() {
    $.ajax('/query/jobstatus', {
        dataType: 'json',
        success: updateStatus
    });
}

function refreshStatusCometSuccess(data, text, xhr) {
    updateStatus(data['status']);
    refreshStatusCometLoop(data['startid'], data['warnid'], data['finishid']);
}

function refreshStatusCometFail(xhr, text, error) {
    $('table#joblist').fadeTo(500, 0.5)
}

function refreshStatusCometLoop(startid, warnid, finishid) {
    $.ajax('/query/jobstatuscomet?startid=' + startid + '&warnid=' + warnid + '&finishid=' + finishid, {
        dataType: 'json',
        success: refreshStatusCometSuccess,
        error: refreshStatusCometFail,
        timeout: 150000
    });
}

$(document).ready(function () {
        //refreshStatus();
        refreshStatusCometLoop(0, 0, 0);

        $('#command_refresh').click(function (event) {
            refreshStatus();
            event.preventDefault();
        });
    });
