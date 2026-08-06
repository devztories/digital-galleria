/* ==========================================
   DIGITAL GALLERIA
   Premium JavaScript
========================================== */

// Sticky Navbar Shadow
window.addEventListener("scroll", () => {

    const navbar = document.querySelector(".navbar");

    if (window.scrollY > 40) {
        navbar.classList.add("shadow-lg");
    } else {
        navbar.classList.remove("shadow-lg");
    }

});


// Smooth Scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {

    anchor.addEventListener("click", function(e){

        e.preventDefault();

        const target = document.querySelector(this.getAttribute("href"));

        if(target){

            target.scrollIntoView({

                behavior:"smooth"

            });

        }

    });

});


// Fade Animation

const observer = new IntersectionObserver((entries)=>{

    entries.forEach(entry=>{

        if(entry.isIntersecting){

            entry.target.classList.add("fade-up");

        }

    });

},{
    threshold:0.2
});

document.querySelectorAll(".dark-card,.hero-section,.product-card")
.forEach(el=>{

    observer.observe(el);

});


// Product Hover Effect

document.querySelectorAll(".product-card").forEach(card=>{

    card.addEventListener("mouseenter",()=>{

        card.style.transform="translateY(-8px)";

    });

    card.addEventListener("mouseleave",()=>{

        card.style.transform="translateY(0px)";

    });

});


// Counter Animation

const counters=document.querySelectorAll(".counter");

counters.forEach(counter=>{

let start=0;

const end=Number(counter.dataset.count);

const speed=30;

const update=()=>{

start++;

counter.innerText=start;

if(start<end){

setTimeout(update,speed);

}

};

update();

});


// Back To Top

const topBtn=document.createElement("button");

topBtn.innerHTML='<i class="fa-solid fa-arrow-up"></i>';

topBtn.className="top-btn";

document.body.appendChild(topBtn);

window.addEventListener("scroll",()=>{

if(window.scrollY>300){

topBtn.classList.add("show");

}else{

topBtn.classList.remove("show");

}

});

topBtn.onclick=()=>{

window.scrollTo({

top:0,

behavior:"smooth"

});

};


// Loading Screen

window.addEventListener("load",()=>{

const loader=document.querySelector(".loader");

if(loader){

loader.style.opacity="0";

setTimeout(()=>{

loader.remove();

},500);

}

});


// Cursor Glow

const glow=document.createElement("div");

glow.className="cursor-glow";

document.body.appendChild(glow);

document.addEventListener("mousemove",(e)=>{

glow.style.left=e.clientX+"px";

glow.style.top=e.clientY+"px";

});