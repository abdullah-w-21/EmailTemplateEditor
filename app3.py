import streamlit as st
from bs4 import BeautifulSoup
import base64
import re


def load_template():
    """Read the template HTML file"""
    with open('template.html', 'r', encoding='utf-8') as file:
        return file.read()


def get_download_link(html_content, filename="modified_template.html"):
    """Generate a download link for the modified HTML"""
    b64 = base64.b64encode(html_content.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{filename}">Download Modified Template</a>'


def is_contact_info(element):
    """Check if element contains contact information"""
    if not element or not element.text.strip():
        return False
    text = element.text.strip().lower()
    return ('email' in text or 'phone' in text or 'contact' in text or
            text.startswith('📧') or text.startswith('📞'))


def find_text_elements(soup):
    """Find all text elements that should be editable"""
    elements = []
    seen_texts = set()  # To track duplicate text content

    # Find all text elements
    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'div', 'span']):
        # Skip empty elements
        text_content = element.text.strip()
        if not text_content:
            continue

        # Skip elements that are part of buttons
        if element.find_parent('a', class_='v-button'):
            continue

        # Skip if element is within specific button structure
        button_parent = element.find_parent('table',
                                            style=lambda x: x and 'font-family:arial,helvetica,sans-serif' in x)
        if button_parent and button_parent.find('a', class_='v-button'):
            continue

        # Skip elements that only contain elements we'll process separately
        if element.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'div', 'span']) and not element.find(string=True,
                                                                                               recursive=False):
            continue

        # Skip duplicate text content
        if text_content in seen_texts:
            continue

        # Add the text content to seen set
        seen_texts.add(text_content)

        # Add element if it has text content
        elements.append(element)

    return elements


def main():
    st.title("Email Template Editor")
    st.write("Edit your email template content and preview the changes in real-time.")

    # Initialize session state
    if 'html_content' not in st.session_state:
        try:
            st.session_state.html_content = load_template()
            st.write("Template file loaded successfully")
        except FileNotFoundError:
            st.error("Template file not found. Please ensure 'template.html' exists in the same directory.")
            return

    if 'wellness_url' not in st.session_state:
        st.session_state.wellness_url = "file:///C:/Users/Administrator/wellness/template.html"
    if 'signup_url' not in st.session_state:
        st.session_state.signup_url = "file:///C:/Users/Administrator/signup/template.html"
    if 'modified_html' not in st.session_state:
        st.session_state.modified_html = st.session_state.html_content
    if 'pending_changes' not in st.session_state:
        st.session_state.pending_changes = {}

    # Create BeautifulSoup object for finding editable elements
    soup = BeautifulSoup(st.session_state.html_content, 'html.parser')
    elements = find_text_elements(soup)

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Edit Content", "Preview", "Export"])

    with tab1:
        st.header("Edit Template Content")

        # Create expandable sections
        body_text = st.expander("Edit Text Content", expanded=True)
        contact_info = st.expander("Contact Information", expanded=True)

        # Combine all text editing into one section
        with body_text:
            st.subheader("Edit All Text Content")
            for i, element in enumerate(elements):
                text_content = element.text.strip()

                # Only show editable box if text length is <= 128 characters
                if len(text_content) <= 128:
                    key = f"text_{element.name}_{i}_{hash(text_content)}"
                    new_text = st.text_input(
                        f"Edit text: {text_content[:50]}...",
                        text_content,
                        key=key
                    )

                    if new_text != text_content:
                        st.session_state.pending_changes[text_content] = new_text

        with contact_info:
            st.subheader("Button Links")

            # Get new URLs from user
            new_wellness_url = st.text_input(
                "Book Wellness Visits Button URL",
                value=st.session_state.wellness_url,
                key="wellness_input"
            )

            new_signup_url = st.text_input(
                "Sign Up for the Program Button URL",
                value=st.session_state.signup_url,
                key="signup_input"
            )

            if new_wellness_url != st.session_state.wellness_url:
                st.session_state.pending_changes[st.session_state.wellness_url] = new_wellness_url

            if new_signup_url != st.session_state.signup_url:
                st.session_state.pending_changes[st.session_state.signup_url] = new_signup_url

            # Social Media Links
            st.subheader("Social Media Links")
            for i, social_link in enumerate(soup.find_all('a', href=re.compile(
                    r'https://(www\.)?(facebook|twitter|instagram|linkedin|x)\.com'))):
                if social_link and social_link.get('href'):
                    platform = social_link['href'].split('.com')[0].split('/')[-1]
                    new_url = st.text_input(
                        f"{platform.capitalize()} URL",
                        social_link['href'],
                        key=f"social_{platform}_{i}"
                    )
                    if new_url != social_link['href']:
                        st.session_state.pending_changes[social_link['href']] = new_url

        # Save button at the bottom of Edit Content tab
        if st.button("Save Changes", type="primary"):
            # Apply all pending changes
            new_html = st.session_state.html_content
            for old_text, new_text in st.session_state.pending_changes.items():
                new_html = new_html.replace(old_text, new_text)

                # Update session state URLs if they were changed
                if old_text == st.session_state.wellness_url:
                    st.session_state.wellness_url = new_text
                elif old_text == st.session_state.signup_url:
                    st.session_state.signup_url = new_text

            # Update the modified HTML
            st.session_state.modified_html = new_html

            # Clear pending changes
            st.session_state.pending_changes = {}

            # Save to file
            output_filename = "modified_template.html"
            with open(output_filename, 'w', encoding='utf-8') as file:
                file.write(new_html)

            st.success("Changes saved successfully!")

    with tab2:
        st.header("Preview")
        st.components.v1.html(st.session_state.modified_html, height=600, scrolling=True)

    with tab3:
        st.header("Export Template")
        st.markdown(get_download_link(st.session_state.modified_html), unsafe_allow_html=True)
        st.text_area("HTML Code", st.session_state.modified_html, height=300)
        if st.button("Copy to Clipboard"):
            st.write("HTML code copied to clipboard!")
            st.session_state['clipboard'] = st.session_state.modified_html


if __name__ == "__main__":
    main()
