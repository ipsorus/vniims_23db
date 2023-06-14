console.log('testing loader')

const spinnerBox=document.getElementById('spinner-box')
const dataBox=document.getElementById('data-box')

$.ajax({
    type: 'GET',
    url: '/spectrum_search/',
    success: function(response){
        console.log('testing success')
        dataBox.classList.add('not-visible')
        setTimeout(()=>{
            spinnerBox.classList.add('not-visible')
            dataBox.classList.remove('not-visible')
            dataBox.innerHTML += }, 500)
    },
    error: function(error){
        console.log('testing error')
        setTimeout(()=>{
            spinnerBox.classList.add('not-visible')
            console.log('testing error not-visible')
            dataBox.innerHTML = `
            <div class="fancy-title title-border title-center">
                <h1>Результатов не найдено.</h1>
            </div>`}, 500)
    },
})