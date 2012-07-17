from mako.template import Template

def report_to_html(report, output, home, base_url):
    template = Template(filename=home + '/templ/report/basic.html')
    return template.render(report=report, output=output, base_url=base_url)
