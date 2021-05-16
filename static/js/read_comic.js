const nav = JSON.parse(document.getElementById('nav').textContent);
const last_read_page = JSON.parse(document.getElementById('last_read_page').textContent);

Reveal.initialize({
    controls: false,
    hash: true,
    width: "100%",
    height: "100%",
    margin: 0,
    minScale: 1,
    maxScale: 1,
    disableLayout: true,
    progress: true,
    keyboard: {
        37: () => {prevPage()},
        39: () => {nextPage()},
        38: () => {window.scrollTo({ top: window.scrollY-window.innerHeight*.6, left: 0, behavior: 'smooth' })},
        40: () => {window.scrollTo({ top: window.scrollY+window.innerHeight*.6, left: 0, behavior: 'smooth' })},
      },
    touch: false,
    transition: 'slide',
    plugins: [ RevealMenu ]
}).then(() => {
    Reveal.slide(last_read_page)

});

Reveal.on( 'slidechanged', event => {
    setTimeout(() =>{document.getElementsByClassName('slides')[0].scrollIntoView({behavior: 'smooth'})}, 100)
    $.ajax({url: "/comic/set_page/" + nav.cur_path + "/" + event.indexh + "/"})
});

const hammertime = new Hammer(document.getElementById('comic_box'), {});
hammertime.on('swipeleft', function (ev) {
    nextPage()
});
hammertime.on('swiperight', function (ev) {
    prevPage()
});

function prevPage() {
    if (Reveal.isFirstSlide()){
        if (nav.prev_type === 'ComicBook'){
            window.location = "/comic/read/"+ nav.prev_path +"/"
        } else {
            window.location = "/comic/"+ nav.prev_path +"/"
        }
    } else {
        Reveal.prev();
    }
}
function nextPage() {
    if (Reveal.isLastSlide()){
        if (nav.next_type === 'ComicBook'){
            window.location = "/comic/read/"+ nav.next_path +"/"
        } else {
            window.location = "/comic/"+ nav.next_path +"/"
        }
    } else {
        Reveal.next()
    }
}
let slides_div = document.getElementById('slides_div')
slides_div.addEventListener('click', nextPage)

let embeds = document.getElementsByClassName('comic_embed')

embeds.forEach(function (embed){
    embed.addEventListener('click', nextPage)
})
