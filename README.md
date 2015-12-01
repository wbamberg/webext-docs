# webext-docs
This repository contains tools for generating MDN documentation for WebExtensions
based on Chrome's JSON API files.

You can generate docs locally as follows:

    mkdir out
    python json-transform.py data/ out windows tabs extension \
        bookmarks cookies i18n browser_action context_menus \
        runtime idle storage web_navigation web_request extension_types events

The output will be generated in files like `out/tabs/create` or
`out/tabs/INDEX` for the page that covers the whole `tabs` namespace.

To upload these files to MDN, do as follows:

    python upload.py out <your-mdn-key-id> <mdn-secret>

Then you can find them at URLs like
`https://developer.allizom.org/en-US/Add-ons/WebExtensions/API/runtime`.
