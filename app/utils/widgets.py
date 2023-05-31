from bs4 import BeautifulSoup

widgets = {
    'calculator': {
        'widget_file': 'app/static/widgets/calculator.html',
        'wrapper_id': 'calculator-wrapper',
        'display_name': 'Calculator',
    },
    'color_picker': {
        'widget_file': 'app/static/widgets/color_picker.html',
        'wrapper_id': 'color-picker-wrapper',
        'display_name': 'Color Picker'
    }
}

def add_widget(html_soup: BeautifulSoup, name: str) -> BeautifulSoup:
    """Adds the a widget to the search results
    Args:
        html_soup: The parsed search result containing the keywords
        name: The name of the widget to be added
    Returns:
        BeautifulSoup
    """
    if not name in widgets:
        # if widget doesn't exist, silently fail
        return
    main_div = html_soup.select_one('#main')
    if main_div:
        widget_file = open(widgets[name]['widget_file'])
        widget_tag = html_soup.new_tag('div')
        widget_tag['class'] = 'ZINbbc xpd O9g5cc uUPGi'
        widget_tag['id'] = widgets[name]['wrapper_id']
        widget_text = html_soup.new_tag('div')
        widget_text['class'] = 'kCrYT ip-address-div'
        widget_text.string = widgets[name]['display_name']
        widget = html_soup.new_tag('div')
        widget.append(BeautifulSoup(widget_file, 'html.parser'));
        widget['class'] = 'kCrYT ip-text-div'
        widget_tag.append(widget_text)
        widget_tag.append(widget)
        main_div.insert_before(widget_tag)
        widget_file.close()
    return html_soup    

def add_ip_card(html_soup: BeautifulSoup, ip: str) -> BeautifulSoup:
    """Adds the client's IP address to the search results
        if query contains keywords

    Args:
        html_soup: The parsed search result containing the keywords
        ip: ip address of the client

    Returns:
        BeautifulSoup

    """
    main_div = html_soup.select_one('#main')
    if main_div:
        # HTML IP card tag
        ip_tag = html_soup.new_tag('div')
        ip_tag['class'] = 'ZINbbc xpd O9g5cc uUPGi'

        # For IP Address html tag
        ip_address = html_soup.new_tag('div')
        ip_address['class'] = 'kCrYT ip-address-div'
        ip_address.string = ip

        # Text below the IP address
        ip_text = html_soup.new_tag('div')
        ip_text.string = 'Your public IP address'
        ip_text['class'] = 'kCrYT ip-text-div'

        # Adding all the above html tags to the IP card
        ip_tag.append(ip_address)
        ip_tag.append(ip_text)

        # Insert the element at the top of the result list
        main_div.insert_before(ip_tag)
    return html_soup
