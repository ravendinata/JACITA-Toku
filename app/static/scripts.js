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

function formatCurrency(value, rounding = 2, symbol = 'IDR')
{
    stringified = value.toFixed(rounding).toString();
    formatted = stringified.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    
    return `${symbol} ${formatted}`;
}

function flashField(fieldId) 
{
    const field = document.getElementById(fieldId);
    if (field) 
    {
        field.classList.add('flash-error');
        setTimeout(() => { field.classList.remove('flash-error'); }, 1000); // Remove the class after 1 second
    }
}

function updateCartItemsCount(orderId)
{
    const badge = document.getElementById('cartCount');

    if (orderId === 'None')
    {
        badge.hidden = true;
        return;
    }
    
    fetch(`/api/order/${orderId}/items/count`)
    .then(response => response.json())
    .then(data => 
    {
        badge.innerHTML = data.total;
        badge.hidden = false;
    });
}

function updateCartTopItems(orderId)
{
    const navCart = document.getElementById('navCart');
    const cartItems = document.getElementById('cartItems');
    const btnOrderDetails = document.getElementById('btnOrderDetails');

    if (orderId == 'None') 
    {
        navCart.hidden = true;
        return;
    }

    btnOrderDetails.hidden = false;
    btnOrderDetails.href = `/order/${orderId}`;

    fetch(`/api/order/${orderId}/items/top`)
    .then(response => response.json())
    .then(data => 
    {
        cartItems.innerHTML = '';
        
        data.forEach(item =>
        {
            const variant = item.variant == '' ? '<i>n/a</i>' : item.variant;
            const cartItem = document.createElement('li');
            cartItem.classList.add('dropdown-item', 'd-flex', 'justify-content-between', 'lh-sm');
            cartItem.innerHTML = 
            `
                <div>
                    <p class="my-0"><strong>${item.brand} ${item.name}</strong></p>
                    <small>Variant: ${variant}</small>
                </div>
                <span><small class="text-muted float-end ms-2">x ${item.quantity} ${item.qty_unit}</small></span>
            `;
            cartItems.appendChild(cartItem);
        }
        );
    }
    );
}

function updateNavbarCart(orderId)
{
    updateCartItemsCount(orderId);
    updateCartTopItems(orderId);
}

function displayToast(title, message, type = 'success', timer = 5000)
{
    const background = document.documentElement.getAttribute('data-bs-theme') == 'dark' ? '#343a40' : '#f8f9fa';
    const forecolor = document.documentElement.getAttribute('data-bs-theme') == 'dark' ? '#f8f9fa' : '#343a40';

    Swal.fire(
    {
        title: title,
        text: message,
        icon: type,
        toast: true,
        position: 'bottom-end',
        showConfirmButton: false,
        timer: timer,
        timerProgressBar: true,
        background: background,
        color: forecolor
    });
}

function displayPopupAlert(title, message, type = 'success')
{
    const background = document.documentElement.getAttribute('data-bs-theme') == 'dark' ? '#343a40' : '#f8f9fa';
    const forecolor = document.documentElement.getAttribute('data-bs-theme') == 'dark' ? '#f8f9fa' : '#343a40';

    Swal.fire(
    {
        title: title,
        text: message,
        icon: type,
        buttonsStyling: false,
        customClass: 
        {
            popUp: 'container',
            confirmButton: 'btn btn-primary mr-2',
            cancelButton: 'btn btn-danger'
        },
        background: background,
        color: forecolor
    });
}

function displayPopupConfirm(title, message, confirmCallback = null, denyCallback = null, confirmText = 'Yes', denyText = 'No')
{
    const background = document.documentElement.getAttribute('data-bs-theme') == 'dark' ? '#343a40' : '#f8f9fa';
    const forecolor = document.documentElement.getAttribute('data-bs-theme') == 'dark' ? '#f8f9fa' : '#343a40';

    Swal.fire(
    {
        title: title,
        text: message,
        icon: 'warning',
        confirmButtonText: confirmText,
        denyButtonText: denyText,
        showDenyButton: true,
        buttonsStyling: false,
        customClass: 
        {
            popUp: 'container',
            confirmButton: 'btn btn-primary mx-2',
            denyButton: 'btn btn-danger mx-2'
        },
        background: background,
        color: forecolor
    }).then((result) => 
    {
        if (result.isConfirmed && confirmCallback != null) 
            confirmCallback();
        else if (result.isDenied && denyCallback != null)
            denyCallback();
    });
}

/* ================================
    LUXON BASED TIME FUNCTIONS
    Requires Luxon.js
================================ */

const DATE_FORMAT = 'yyyy/MM/dd - HH:mm:ss';

function formatToLocalTZ(date, source_zone, append_relative = false)
{
    const dateLocalTZ = luxon.DateTime.fromISO(date, { zone: source_zone }).setZone('system');
    
    if (append_relative)
    {
        const relativeDate = getRelativeTime(date, source_zone);
        return `${dateLocalTZ.toFormat(DATE_FORMAT)}<br><small>${relativeDate}</small>`;
    }
    else
        return dateLocalTZ.toFormat(DATE_FORMAT);
}

function getRelativeTime(date, source_zone)
{
    const dateLocalTZ = luxon.DateTime.fromISO(date, { zone: source_zone }).setZone('system');
    const now = luxon.DateTime.local();
    const diff = now.diff(dateLocalTZ, ['months', 'days', 'hours', 'minutes', 'seconds']);

    if (diff.months > 0) return `${diff.months} month(s) ago`;
    else if (diff.days > 0) return `${diff.days} day(s) ago`;
    else if (diff.hours > 0) return `${diff.hours} hour(s) ago`;
    else if (diff.minutes > 0) return `${diff.minutes} minute(s) ago`;
    else if (diff.seconds > 0) return `${diff.seconds} second(s) ago`;
    else return 'Just now';
}