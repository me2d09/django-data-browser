(this.webpackJsonpfrontend=this.webpackJsonpfrontend||[]).push([[0],[,,,function(e,t,a){e.exports=a(10)},,,,,function(e,t,a){},function(e,t,a){},function(e,t,a){"use strict";a.r(t);var n=a(0),l=a.n(n),r=a(2),c=a.n(r);a(8),a(9);function m(e){return l.a.createElement(l.a.Fragment,null,e.fields.map((function(e){return l.a.createElement(l.a.Fragment,null,e.concrete?l.a.createElement("a",{href:e.add_filter_link},"Y"):l.a.createElement(l.a.Fragment,null,"\xa0\xa0")," ",l.a.createElement("a",{href:e.add_link},e.name),l.a.createElement("br",null))})),e.fks.map((function(e){return l.a.createElement(l.a.Fragment,null,l.a.createElement("button",{className:"link toggle_link"},"+ ",e.name),l.a.createElement("div",{class:"toggle_div",id:"toggle__"+e.path},l.a.createElement(m,e)))})))}function o(e){return l.a.createElement("div",{id:"body"},l.a.createElement("h1",null,e.query.model),l.a.createElement("p",null,l.a.createElement("a",{href:e.query.csv_link},"Download as CSV")),l.a.createElement("p",null,l.a.createElement("a",{href:e.query.save_link},"Save View")),l.a.createElement("form",{className:"filters",method:"get",action:e.query.base_url},e.query.filters.map((function(e){return l.a.createElement("p",{className:!e.is_valid&&"error"},l.a.createElement("a",{href:e.remove_link},"\u2718")," ",e.name," ",l.a.createElement("select",{defaultValue:e.lookup},e.lookups.map((function(e){return l.a.createElement("option",{value:e.name},e.name)})))," = ",l.a.createElement("input",{type:"text",name:e.url_name,value:e.value}))})),l.a.createElement("p",null,l.a.createElement("input",{type:"submit"})),l.a.createElement("p",null,"Showing ",e.data.length," results")),l.a.createElement("div",{className:"main_space"},l.a.createElement("div",null,l.a.createElement(m,e.query.all_fields_nested)),l.a.createElement("table",null,l.a.createElement("tr",null,e.query.sort_fields.map((function(e){var t=e.field,a=e.sort_icon;return l.a.createElement("th",null,l.a.createElement("a",{href:t.remove_link},"\u2718")," ",t.concrete?l.a.createElement(l.a.Fragment,null,l.a.createElement("a",{href:t.add_filter_link},"Y")," ",l.a.createElement("a",{href:t.toggle_sort_link},t.name)," ",a):t.name)})),!e.query.sort_fields.length&&l.a.createElement("th",null,"No fields selected")),e.data.map((function(e){return l.a.createElement("tr",null,e.map((function(e){return l.a.createElement("td",null,e)})))})))))}var u=function(){var e=JSON.parse(document.getElementById("django-data").textContent);return l.a.createElement(o,e)};Boolean("localhost"===window.location.hostname||"[::1]"===window.location.hostname||window.location.hostname.match(/^127(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}$/));c.a.render(l.a.createElement(l.a.StrictMode,null,l.a.createElement(u,null)),document.getElementById("root")),"serviceWorker"in navigator&&navigator.serviceWorker.ready.then((function(e){e.unregister()})).catch((function(e){console.error(e.message)}))}],[[3,1,2]]]);
//# sourceMappingURL=main.e1324543.chunk.js.map