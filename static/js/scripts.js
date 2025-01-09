/*!
* Start Bootstrap - Simple Sidebar v6.0.6 (https://startbootstrap.com/template/simple-sidebar)
* Copyright 2013-2023 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-simple-sidebar/blob/master/LICENSE)
*/
// 
// Scripts
// 

window.addEventListener('DOMContentLoaded', event => {
    const sidebarToggle = document.getElementById('sidebarToggle');
    
    if (sidebarToggle) {
        // Handle sidebar toggle
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
            
            // Close sidebar when clicking outside on mobile
            if (window.innerWidth < 769) {
                document.addEventListener('click', function closeMenu(e) {
                    if (document.body.classList.contains('sb-sidenav-toggled') && 
                        !document.getElementById('sidebar-wrapper').contains(e.target) &&
                        !sidebarToggle.contains(e.target)) {
                        document.body.classList.remove('sb-sidenav-toggled');
                        document.removeEventListener('click', closeMenu);
                    }
                });
            }
        });
    }
    
    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            if (window.innerWidth >= 769) {
                document.body.classList.remove('sb-sidenav-toggled');
            }
        }, 250);
    });
});
