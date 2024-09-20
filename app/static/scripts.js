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

function updateCartItemsCount()
{
    const order_id = getCookie('order_id');
    const badge = document.getElementById('cartCount');

    if (order_id === '' || order_id == null) 
    {
        badge.hidden = true;
        return;
    }
    
    fetch(`/api/order/${order_id}/items/count`)
    .then(response => response.json())
    .then(data => 
    {
        badge.innerHTML = data.total;
        badge.hidden = false;
    });
}

function updateCartTopItems()
{
    const order_id = getCookie('order_id');
    const cartItems = document.getElementById('cartItems');
    const btnOrderDetails = document.getElementById('btnOrderDetails');

    if (order_id === '' || order_id == null) 
    {
        cartItems.innerHTML = '';

        const cartItem = document.createElement('li');
        cartItem.classList.add('dropdown-item', 'd-flex', 'justify-content-between', 'lh-sm');
        cartItem.innerHTML = '<small class="text-muted">No active order</small>';
        cartItems.appendChild(cartItem);

        btnOrderDetails.hidden = true;

        return;
    }

    btnOrderDetails.hidden = false;
    btnOrderDetails.href = `/order/${order_id}`;

    fetch(`/api/order/${order_id}/items/top`)
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