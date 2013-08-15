$(document).ready(function () {
    // Check for an ANSI converter function.
    var ansi_to_html;

    if (typeof ansi_up !== 'undefined') {
        ansi_to_html = ansi_up.ansi_to_html;
    }

    // If we have an ANSI converter and the output appears
    // to include escape sequences, add a control which
    // can be used to run the output through the converter.
    if (typeof ansi_to_html !== 'undefined') {
        $('.joboutput').each(function (index) {
            var joboutput = $(this);
            if (joboutput.html().search(/\033\[/) != -1) {
                var colorpara = $.parseHTML('<p></p>');
                var colorlink = $.parseHTML(
                    '<a href="#"><span class="icon-adjust"></span> Display ANSI colors.</a>');
                joboutput.before(colorpara);
                $(colorpara).append(colorlink);
                $(colorlink).click(function (event) {
                    $(colorlink).hide();
                    joboutput.parent().css('color', 'white');
                    joboutput.parent().css('background-color', 'black');
                    joboutput.html(ansi_to_html(joboutput.html()));
                    event.preventDefault();
                });
            }
        });
    }
});
