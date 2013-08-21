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
                var colorinvert = 0;
                var colorpara = $.parseHTML('<p></p>');
                var invertpara = $.parseHTML('<p class="hidden"></p>');
                var colorlink = $.parseHTML(
                    '<a href="#"><span class="icon-adjust"></span> Display ANSI colors.</a>');
                var invertlink = $.parseHTML(
                    '<a href="#"><span class="icon-exchange"></span> Invert colors.</a>');
                joboutput.before(colorpara);
                joboutput.before(invertpara);
                $(colorpara).append(colorlink);
                $(invertpara).append(invertlink);
                $(colorlink).click(function (event) {
                    $(colorpara).hide();
                    $(invertpara).show();
                    joboutput.html(ansi_to_html(joboutput.html()));
                    event.preventDefault();
                });
                $(invertlink).click(function (event) {
                    colorinvert = colorinvert ? 0 : 1;
                    var fg = colorinvert ? 'white' : 'black';
                    var bg = colorinvert ? 'black' : 'white';
                    joboutput.parent().css('color', fg);
                    joboutput.parent().css('background-color', bg);
                    event.preventDefault();
                });
            }
        });
    }
});
