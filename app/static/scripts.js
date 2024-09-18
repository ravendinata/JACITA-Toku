const params = new URLSearchParams(window.location.search);
const normalize = params.has('norm');

// Set the theme
if (getCookie('theme') == 'dark')
document.documentElement.setAttribute('data-bs-theme', 'dark')
else
document.documentElement.setAttribute('data-bs-theme', 'light')

// On ready
$(document).ready(function ()
{    
    // Normalize the URL
    if (normalize)
        window.history.replaceState({}, document.title, window.location.pathname);

    // Fade out the alert if it exists
    $('#alert').fadeTo(5000, 500).slideUp(500, function ()
    {
        $('#alert').slideUp(500);
    });
});

// Toggle color mode
document.getElementById('btnToggleColorMode').addEventListener('click', () =>
{
    if (document.documentElement.getAttribute('data-bs-theme') == 'dark')
    {
        document.documentElement.setAttribute('data-bs-theme', 'light')
        setCookie('theme', 'light', 365)
    }
    else
    {
        document.documentElement.setAttribute('data-bs-theme', 'dark')
        setCookie('theme', 'dark', 365)
    }
});

// Functions
function setCookie(name, value, days) 
{
    var expires = "";
    
    if(days) 
    {
        var date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }

    document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

function getCookie(name) 
{
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');

    for(var i = 0; i < ca.length; i++) 
    {
        var c = ca[i];

        while (c.charAt(0) == ' ') 
            c = c.substring(1, c.length);
        
        if (c.indexOf(nameEQ) == 0) 
            return c.substring(nameEQ.length, c.length);
    }

    return null;
}

function removeCookie(name)
{
    document.cookie = name + '=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
}

function wipeCookie(name) { document.cookie = name +'=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;'; }