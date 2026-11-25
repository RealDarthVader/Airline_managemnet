const menu = document.querySelector('.menu-toggle');
const backdrop = document.querySelector('.nav-backdrop');
const sidebar = document.querySelector('.sidebar');

function setMenu(open) {
  document.body.classList.toggle('nav-open', open);
  menu.setAttribute('aria-expanded', String(open));
  menu.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
  if (open) sidebar.querySelector('[aria-current="page"], a').focus();
  else menu.focus();
}

menu.addEventListener('click', () => setMenu(!document.body.classList.contains('nav-open')));
backdrop.addEventListener('click', () => setMenu(false));
document.addEventListener('keydown', event => {
  if (!document.body.classList.contains('nav-open')) return;
  if (event.key === 'Escape') setMenu(false);
  if (event.key === 'Tab') {
    const links = sidebar.querySelectorAll('a');
    const boundary = event.shiftKey ? links[0] : links[links.length - 1];
    if (document.activeElement === boundary) {
      event.preventDefault();
      (event.shiftKey ? links[links.length - 1] : links[0]).focus();
    }
  }
});
