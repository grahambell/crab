$(document).ready(function () {
    var sortByStatus = false;
    var disconnectFavicon = null;

    // Need to load the disconnected icon now because if the
    // server vanishes we will not be able to load it when
    // needed.
    (function () {
        var image = new Image();

        image.onload = function () {
            var canvas = document.createElement('canvas');
            canvas.width = 16;
            canvas.height = 16;
            var context = canvas.getContext('2d');
            context.drawImage(image, 0, 0);
            disconnectFavicon = canvas.toDataURL('image/png');
        };

        image.src = '/res/favicon-disconnect.png';
    })();

    // Find the status_running CSS rule and make it flash.
    (function () {
        var runningRule = null;
        var runningRuleOn = false;

        for (var i = 0; i < document.styleSheets.length; i ++) {
            var sheet = document.styleSheets[i];
            for (var j = 0; j < sheet.cssRules.length; j++) {
                var rule = sheet.cssRules[j];
                if (rule.selectorText === '.status_running') {
                    runningRule = rule;
                }
            }
        }

        if (runningRule !== null) {
            setInterval(function () {
                runningRuleOn = ! runningRuleOn;
                if (runningRuleOn) {
                    runningRule.style.cssText = 'opacity: 0.25;';
                }
                else {
                    runningRule.style.cssText = 'opacity: 1.0;';
                }
            }, 500);
        }
    })();

    // Set up table sorting controls.
    $('#headingstatus').click(function (event) {
        var tab = $('#joblistbody');
        tab.append(tab.children().has('.status_ok').detach());
        tab.prepend(tab.children().has('.status_warn').detach());
        tab.prepend(tab.children().has('.status_fail').detach());
        sortByStatus = true;
        $('#joblisthead span').removeClass();
        $('#preheadingstatus').addClass('fa fa-sort');
        event.preventDefault();
    });

    var dashboardSorter = (function (keyfield) {
        var sortdirection = 1;

        return function (event) {
            var arr = new Array();
            var tab = $('#joblistbody');

            tab.children().each(function (index) {
                arr.push({row: this, text: $(this).find('[id^=' + keyfield + '_]').text()});
            });

            arr.sort(function (a, b) {
                return a.text == b.text ? 0 : sortdirection * (a.text < b.text ? -1 : 1);
            });

            for (var i in arr) {
                tab.append($(arr[i].row).detach());
            }

            $('#joblisthead span').removeClass();
            $('#preheading' + keyfield).addClass('fa fa-sort-' + (sortdirection > 0 ? 'down' : 'up'));

            sortdirection = - sortdirection;
            sortByStatus = false;
            event.preventDefault();
        };
    });

    $('#headinghost').click(dashboardSorter('host'));
    $('#headinguser').click(dashboardSorter('user'));
    $('#headingcrabid').click(dashboardSorter('crabid'));
    $('#headingcommand').click(dashboardSorter('command'));
    $('#headingreliability').click(dashboardSorter('reliability'));

    // Refresh functionality.
    var updateStatusBox = (function (id, status_, running) {
        var box = $('#status_' + id);
        if (status_ === null) {
            box.text('Unknown');
            box.removeClass().addClass('status_unknown');
        }
        else {
            box.text(crabStatusName(status_));
            if (crabStatusIsOK(status_)) {
                box.removeClass().addClass('status_ok');
            }
            else if (crabStatusIsWarning(status_)) {
                if (! box.hasClass('status_warn')) {
                    box.removeClass().addClass('status_warn');

                    if (sortByStatus) {
                        var tab = $('#joblistbody');
                        tab.prepend($('#row_' + id).detach());
                    }
                }
            }
            else if (! box.hasClass('status_fail')) {
                box.removeClass().addClass('status_fail');

                if (sortByStatus) {
                    var tab = $('#joblistbody');
                    tab.prepend($('#row_' + id).detach());
                }
            }
        }
        if (running) {
            box.addClass('status_running');
        } else if (box.hasClass('status_running')) {
            box.removeClass('status_running');
        }
    });

    var updateReliabilityBox = (function (id, reliability) {
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
            stars = stars.concat('&#x2605;');
            reliability -= 20;
        }
        if (reliability >= 10) {
            stars = stars.concat('&#x2606;');
        }
        box.html(stars);
        box.removeClass().addClass('status_normal');
    });

    var setFavicon = (function (url) {
        var favicon = $('link[rel=icon]');
        favicon.replaceWith(favicon.clone().attr('href', url));
    });

    var updateServiceStatus = (function (servstatus) {
        var statustext = '';
        for (var id in servstatus) {
            if (servstatus[id]) {
                statustext = statustext.concat('<li class="status_ok">');
            }
            else {
                statustext = statustext.concat('<li class="status_fail">');
            }
            statustext = statustext.concat(id + '</li> ');
        }
        $('#service_status').html(statustext);
    });

    var updateStatus = (function (data) {
        var statusdata = data['status'];
        for (var id in statusdata) {
            var job = statusdata[id];

            if ($('#row_' + id).length == 0) {
                $('table#joblist').append(joblistrowtemplate.replace(new RegExp('XXX', 'g'), id));
                $.ajax('/query/jobinfo/' + id, {
                    dataType: 'json',
                }).done(function (data) {
                    var id = data['id'];
                    $('#host_' + id).text(data['host']);
                    $('#user_' + id).text(data['user']);
                    $('#command_' + id).text(data['command']);
                    if (data['crabid'] !== null) {
                        $('#crabid_' + id).text(data['crabid']);
                        $('#crabid_' + id).removeClass();
                    }
                });
            }

            updateStatusBox(id, job['status'], job['running']);
            updateReliabilityBox(id, job['reliability']);

            if (! job['scheduled']) {
                $('#reliability_' + id).append('<span title="The schedule for this job is unknown.">&#x26A0;</span>');
            }
        }

        var current_time = new Date();
        $('#last_refresh').text(current_time.toString());

        updateServiceStatus(data['service']);

        var service_ok = true;
        for (var id in data['service']) {
            service_ok = service_ok && data['service'][id];
        }

        if (! service_ok) {
            setFavicon('/res/favicon-stopped.png');
        }
        else if (data['numerror'] > 0) {
            setFavicon('/res/favicon-error.png');
        }
        else if (data['numwarning'] > 0) {
            setFavicon('/res/favicon-warn.png');
        }
        else {
            setFavicon('/res/favicon.png');
        }
    });

    var refreshStatusCometLoop = (function (startid, alarmid, finishid) {
        $.ajax('/query/jobstatus?startid=' + startid + '&alarmid=' + alarmid + '&finishid=' + finishid, {
            dataType: 'json',
            timeout: 160000
        }).done(function (data, text, xhr) {
            updateStatus(data);
            refreshStatusCometLoop(data['startid'], data['alarmid'], data['finishid']);
        }).fail(function (xhr, text, error) {
            setTimeout((function () {
                refreshStatusCometLoop(0, 0, 0);
                $('table#joblist').fadeTo(500, 1.0);
            }), 600000);
            $('table#joblist').fadeTo(500, 0.3);
            if (disconnectFavicon !== null) {
                setFavicon(disconnectFavicon);
            }
        });
    });

    $('#command_refresh').click(function (event) {
        $('#command_refresh').children('span').addClass('fa-spin');

        $.ajax('/query/jobstatus?startid=0&alarmid=0&finishid=0', {
            dataType: 'json',
        }).done(function (data, text, xhr) {
            updateStatus(data);
        }).fail(function (xhr, text, error) {
            $('#last_refresh').text('Failed to fetch status from server.');
        }).always(function () {
            $('#command_refresh').children('span').removeClass('fa-spin');
        });

        event.preventDefault();
    });

    refreshStatusCometLoop(0, 0, 0);
});
