(function () {
  var HASH = 'd4d9697ab78873b1ca7154554d701f278de4ab4abe26595c8556d3159f9727e7';
  var KEY = 'afd_gate';
  var root = document.documentElement;

  function sha256(text) {
    var data = new TextEncoder().encode('aifordaniel.pro::' + text);
    return crypto.subtle.digest('SHA-256', data).then(function (buf) {
      return Array.prototype.map.call(new Uint8Array(buf), function (b) {
        return ('0' + b.toString(16)).slice(-2);
      }).join('');
    });
  }

  var stored = null;
  try { stored = localStorage.getItem(KEY); } catch (e) {}
  if (stored === HASH) return;

  var hide = document.createElement('style');
  hide.id = 'afd-hide';
  hide.textContent = 'html{overflow:hidden!important}body{visibility:hidden!important}';
  document.head.appendChild(hide);

  function unlock() {
    var o = document.getElementById('afd-gate');
    if (o) o.remove();
    hide.remove();
  }

  function build() {
    var o = document.createElement('div');
    o.id = 'afd-gate';
    o.setAttribute('dir', 'rtl');
    o.style.cssText = 'position:fixed;inset:0;z-index:2147483647;display:flex;align-items:center;justify-content:center;background:#0e0f12;font-family:system-ui,-apple-system,"Segoe UI",Arial,sans-serif;color:#f3f3f3;padding:24px';
    o.innerHTML =
      '<form id="afd-form" style="width:100%;max-width:340px;text-align:center">' +
      '<div style="font-size:42px;margin-bottom:12px">🔒</div>' +
      '<h1 style="font-size:22px;font-weight:600;margin:0 0 6px">האתר סגור</h1>' +
      '<p style="margin:0 0 20px;color:#9aa0a6;font-size:15px">הכנס סיסמה כדי להמשיך</p>' +
      '<input id="afd-pw" type="password" inputmode="numeric" maxlength="8" autocomplete="off" autofocus placeholder="סיסמה" style="width:100%;box-sizing:border-box;padding:14px 16px;border-radius:12px;border:1px solid #2d3036;background:#17181c;color:#fff;font-size:18px;text-align:center;outline:none">' +
      '<button type="submit" style="width:100%;margin-top:12px;padding:14px;border:0;border-radius:12px;background:#f3f3f3;color:#0e0f12;font-size:17px;font-weight:600;cursor:pointer">כניסה</button>' +
      '<p id="afd-err" style="min-height:20px;margin:12px 0 0;color:#ff6b6b;font-size:14px"></p>' +
      '</form>';
    root.appendChild(o);
    var pw = document.getElementById('afd-pw');
    var err = document.getElementById('afd-err');
    pw.focus();
    document.getElementById('afd-form').addEventListener('submit', function (ev) {
      ev.preventDefault();
      if (!(window.crypto && crypto.subtle)) {
        err.textContent = 'הדפדפן לא תומך. פתח דרך https.';
        return;
      }
      sha256(pw.value.trim()).then(function (h) {
        if (h === HASH) {
          try { localStorage.setItem(KEY, h); } catch (e) {}
          unlock();
        } else {
          err.textContent = 'סיסמה שגויה';
          pw.value = '';
          pw.focus();
        }
      });
    });
  }

  if (document.body) build();
  else document.addEventListener('DOMContentLoaded', build);
})();
