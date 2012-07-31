from mako.template import Template

def report_to_html(report, home, base_url):
    template = Template(filename=home + '/templ/report/basic.html')
    return template.render(report=report, base_url=base_url)
