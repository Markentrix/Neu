// Nur beim Öffnen per Doppelklick (file://): Links auf die .html-Dateien umbiegen,
// damit die Navigation auch ohne Server funktioniert. Auf dem Server macht dieses Skript nichts.
(function () {
  if (location.protocol !== "file:") return;
  document.querySelectorAll("a[href]").forEach(function (a) {
    var href = a.getAttribute("href");
    if (/^([a-z]+:|#|\/\/)/i.test(href)) return;
    var m = href.match(/^([^?#]*)(.*)$/);
    var path = m[1], rest = m[2];
    if (path === "" ) return;
    if (path === "." || path === ".." || /\/$/.test(path)) path = path.replace(/\/?$/, "/") + "index.html";
    else if (!/\.[a-z0-9]+$/i.test(path)) path += ".html";
    a.setAttribute("href", path + rest);
  });
})();
