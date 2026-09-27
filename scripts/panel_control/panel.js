(function () {
  "use strict";

  var ENTORNOS = ["prod", "dev", "staging", "test"];
  var COMPONENTES = [
    { id: "backend", nombre: "Backend" },
    { id: "ux", nombre: "Ux" },
    { id: "pwa", nombre: "PWA" },
  ];

  function svgReiniciar() {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">' +
      '<path d="M4 12a8 8 0 1 1 3 6.3"/><path d="M4 20v-5h5"/></svg>';
  }
  function svgLog() {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">' +
      '<path d="M7 3h8l4 4v14H7z"/><path d="M15 3v4h4"/><path d="M9 13h6M9 17h6"/></svg>';
  }
  function svgHistorial() {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">' +
      '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>';
  }

  function armarTabs() {
    var contenedor = document.getElementById("tabPanels");
    ENTORNOS.forEach(function (entorno, i) {
      var panel = document.createElement("div");
      panel.className = "tab-panel" + (i === 0 ? " is-active" : "");
      panel.dataset.panel = entorno;
      COMPONENTES.forEach(function (c) {
        panel.appendChild(armarFila(entorno, c.id, c.nombre));
      });
      contenedor.appendChild(panel);
    });

    document.querySelectorAll(".tab").forEach(function (tab) {
      tab.addEventListener("click", function () {
        document.querySelectorAll(".tab").forEach(function (t) { t.classList.remove("is-active"); });
        document.querySelectorAll(".tab-panel").forEach(function (p) { p.classList.remove("is-active"); });
        tab.classList.add("is-active");
        document.querySelector('.tab-panel[data-panel="' + tab.dataset.tab + '"]').classList.add("is-active");
      });
    });
  }

  function armarFila(entorno, componente, nombre) {
    var row = document.createElement("div");
    row.className = "row";
    row.id = "row-" + entorno + "-" + componente;

    var dot = document.createElement("span");
    dot.className = "dot off";
    dot.id = "dot-" + entorno + "-" + componente;
    row.appendChild(dot);

    var main = document.createElement("div");
    main.className = "row-main";
    var rn = document.createElement("span");
    rn.className = "row-name";
    rn.textContent = nombre;
    var rs = document.createElement("span");
    rs.className = "row-sub";
    rs.id = "sub-" + entorno + "-" + componente;
    rs.textContent = "cargando...";
    main.appendChild(rn);
    main.appendChild(rs);
    row.appendChild(main);

    row.appendChild(Object.assign(document.createElement("span"), { className: "spacer" }));

    var link = document.createElement("a");
    link.className = "port-link mono";
    link.id = "link-" + entorno + "-" + componente;
    link.hidden = true;
    link.addEventListener("click", function () {
      var url = link.dataset.url;
      if (url) llamarApi("abrir_link", [url]);
    });
    row.appendChild(link);

    var toggle = document.createElement("button");
    toggle.className = "toggle";
    toggle.id = "toggle-" + entorno + "-" + componente;
    toggle.hidden = true;
    toggle.addEventListener("click", function () {
      if (toggle.disabled) return;
      var accion = toggle.classList.contains("is-on") ? "detener" : "iniciar";
      toggle.disabled = true;
      llamarApi(accion, [componente, entorno]).then(refrescar).finally(function () { toggle.disabled = false; });
    });
    row.appendChild(toggle);

    var restart = document.createElement("button");
    restart.className = "icon-btn";
    restart.id = "restart-" + entorno + "-" + componente;
    restart.hidden = true;
    restart.title = "Reiniciar";
    restart.innerHTML = svgReiniciar();
    restart.addEventListener("click", function () {
      llamarApi("reiniciar", [componente, entorno]).then(refrescar);
    });
    row.appendChild(restart);

    return row;
  }

  function llamarApi(metodo, args) {
    if (window.pywebview && window.pywebview.api && window.pywebview.api[metodo]) {
      return window.pywebview.api[metodo].apply(null, args || []);
    }
    console.warn("pywebview.api." + metodo + " no disponible (modo demo)");
    return Promise.resolve(null);
  }

  function aplicarEstadoFila(e) {
    var key = e.entorno + "-" + e.componente;
    var dot = document.getElementById("dot-" + key);
    var sub = document.getElementById("sub-" + key);
    var link = document.getElementById("link-" + key);
    var toggle = document.getElementById("toggle-" + key);
    var restart = document.getElementById("restart-" + key);
    if (!dot) return;

    dot.className = "dot " + (e.salud === "n/a" ? "off" : e.salud);
    sub.textContent = e.detalle;
    sub.title = e.detalle;

    if (e.puerto) {
      link.hidden = false;
      link.dataset.url = "http://localhost:" + e.puerto;
      link.textContent = ":" + e.puerto;
    } else if (e.componente === "pwa") {
      link.hidden = false;
      link.dataset.url = e.link_publicado || "";
      link.textContent = "abrir";
    } else {
      link.hidden = true;
    }

    var controlable = e.salud !== "n/a";
    toggle.hidden = !controlable;
    restart.hidden = !controlable;
    if (controlable) {
      toggle.classList.remove("state-ok", "state-warn", "state-off");
      toggle.classList.add("state-" + (e.salud === "off" ? "off" : e.salud));
      toggle.classList.toggle("is-on", e.salud !== "off");
      restart.disabled = e.salud === "off";
    }
  }

  function aplicarTabDots() {
    ENTORNOS.forEach(function (entorno) {
      var peor = "off";
      COMPONENTES.forEach(function (c) {
        var dot = document.getElementById("dot-" + entorno + "-" + c.id);
        if (!dot) return;
        if (dot.classList.contains("warn")) peor = "warn";
        else if (dot.classList.contains("ok") && peor !== "warn") peor = "ok";
      });
      var tabDot = document.querySelector('[data-tabdot="' + entorno + '"]');
      if (tabDot) tabDot.style.background = "var(--" + peor + ")";
    });
  }

  function aplicarTarea(t) {
    var cont = document.getElementById("tareaRow");
    cont.innerHTML = "";

    var row = document.createElement("div");
    row.className = "row";
    // ultima_corrida_ok viene de los errores reales registrados (misma
    // fuente que el detalle de historial) -- no del "Last Result" crudo de
    // Task Scheduler, que usa codigos como "corriendo ahora mismo" o
    // "todavia no corrio" que no son fallas y generaban falsos rojos aca
    // mientras el historial de abajo mostraba todo en verde.
    var salud = "off";
    var subTexto = "sin datos";
    if (t && t.existe) {
      if (t.ultima_corrida_ok === true) { salud = "ok"; subTexto = "ultima corrida: OK"; }
      else if (t.ultima_corrida_ok === false) { salud = "crit"; subTexto = "ultima corrida: con errores"; }
      else { salud = "off"; subTexto = "sin corridas registradas todavia"; }
    }
    row.innerHTML =
      '<span class="dot ' + salud + '"></span>' +
      '<div class="row-main">' +
        '<span class="row-name">Import PWA -> escritorio</span>' +
        '<span class="row-sub mono">' + subTexto + '</span>' +
      '</div>' +
      '<span class="spacer"></span>' +
      '<button class="icon-btn" id="btnHistorial" title="Ver historial de corridas">' + svgHistorial() + '</button>';
    cont.appendChild(row);
    document.getElementById("btnHistorial").addEventListener("click", abrirHistorial);

    var placeholder = document.createElement("div");
    placeholder.className = "row";
    placeholder.style.opacity = ".55";
    placeholder.innerHTML =
      '<span class="dot off"></span>' +
      '<div class="row-main">' +
        '<span class="row-name">ETL correo/PDF (Claude Desktop)</span>' +
        '<span class="row-sub">no implementado todavia</span>' +
      '</div>';
    cont.appendChild(placeholder);
  }

  function abrirHistorial() {
    document.querySelector('.view-main').classList.remove("is-active");
    document.querySelector('.view-history').classList.add("is-active");
    llamarApi("historial", [20]).then(function (filas) {
      var cont = document.getElementById("historyRows");
      cont.innerHTML = "";
      filas = filas || [];
      if (!filas.length) {
        cont.innerHTML = '<div class="hist-row"><span class="row-sub">Sin corridas registradas todavia.</span></div>';
      }
      filas.forEach(function (f) {
        var salud = f.errores > 0 ? "crit" : "ok";
        var resumen = f.archivos_leidos + " archivos - " + f.transacciones_nuevas + " nuevas - " +
          f.duplicados + " duplicados - " + f.errores + " errores";
        var row = document.createElement("div");
        row.className = "hist-row";
        row.innerHTML =
          '<span class="dot ' + salud + '"></span>' +
          '<div class="row-main">' +
            '<span class="row-name mono">' + (f.fecha_inicio || "") + '</span>' +
            '<span class="row-sub" title="' + resumen + '">' + resumen + '</span>' +
          '</div>' +
          '<button class="icon-btn" title="Ver notas de esta corrida">' + svgLog() + '</button>';
        row.querySelector(".icon-btn").addEventListener("click", function () {
          alert(f.notas || "(sin notas)");
        });
        cont.appendChild(row);
      });
      document.getElementById("historyFoot").textContent = "ultimas " + filas.length + " corridas";
    });
  }

  function refrescar() {
    llamarApi("estado_todos").then(function (estados) {
      (estados || []).forEach(aplicarEstadoFila);
      aplicarTabDots();
    });
    llamarApi("tarea_estado").then(aplicarTarea);
    document.getElementById("footUpdated").textContent = "actualizado " + new Date().toLocaleTimeString();
  }

  document.getElementById("historyBack").addEventListener("click", function () {
    document.querySelector('.view-history').classList.remove("is-active");
    document.querySelector('.view-main').classList.add("is-active");
  });
  document.getElementById("abrirLogs").addEventListener("click", function () {
    llamarApi("abrir_carpeta_logs");
  });

  armarTabs();
  window.addEventListener("pywebviewready", refrescar);
  refrescar(); // primer intento inmediato (modo demo si pywebview todavia no esta listo)
  setInterval(refrescar, 5000);
})();
