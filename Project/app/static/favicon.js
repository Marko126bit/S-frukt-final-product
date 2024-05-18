(function() {
    var head = document.getElementsByTagName('head')[0];
  
    // Function to add a link element
    function addLink(rel, sizes, href) {
      var link = document.createElement('link');
      link.rel = rel;
      if (sizes) link.sizes = sizes;
      link.href = href;
      head.appendChild(link);
    }
  
    // Favicon ICO
    addLink('shortcut icon', null, '/static/favedit.ico');
  
    // Apple Touch Icon
    addLink('apple-touch-icon', '180x180', '/static/apple-touch-icon.png');
  
    // Favicon PNGs
    addLink('icon', '32x32', '/static/favicon-32x32.png');
    addLink('icon', '16x16', '/static/favicon-16x16.png');
  
    // Android Chrome Icons
    addLink('icon', '192x192', '/static/android-chrome-192x192.png');
    addLink('icon', '512x512', '/static/android-chrome-512x512.png');
  
    // Manifest for the web application
    addLink('manifest', null, '/static/manifest.json');
  })();
  


