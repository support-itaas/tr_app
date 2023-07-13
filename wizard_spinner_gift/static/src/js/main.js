function shuffle(array) {
  var currentIndex = array.length,
    randomIndex;
  while (0 !== currentIndex) {
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex--;
    [array[currentIndex], array[randomIndex]] = [
      array[randomIndex],
      array[currentIndex],
    ];
  }
  return array;
}

function spin() {
  // Inisialisasi variabel
  const box = document.getElementById("box");
  const element = document.getElementById("mainbox");
  var partner = $('#res_partner').val();

  let SelectedItem = "";
  //  let Hasil = shuffle([1890, 2250, 2610, 1850, 2210, 2570, 1810, 2170, 2530, 1770, 2130, 2490, 1750, 2110, 2470, 1630, 1990, 2350, 1570, 1930, 2290]);
  $.ajax({
    url: '/spinner_gifts',
    type: 'GET',
    data: {
      partner: partner
    },
    success: function(response) {
      console.log("res2", response)
      var data = JSON.parse(response);
      var degree = parseInt(data.random)
      SelectedItem = data.gift_name;
      box.style.setProperty("transition", "all ease 5s");
      box.style.transform = "rotate(" + degree + "deg)";
      element.classList.remove("animate");
      setTimeout(function() {
        element.classList.add("animate");
      }, 5000);
      setTimeout(function() {
        swal({
          title: "Congratulations",
          text: "You Won " + SelectedItem + " !",
          imageUrl: 'https://media.giphy.com/media/1itd8X8whi3eOgZSRW/giphy.gif'
        });
      }, 5000);
      // Delay and set to normal state
      setTimeout(function() {
        box.style.setProperty("transition", "initial");
        box.style.transform = "rotate(90deg)";
      }, 5500);
      setTimeout(function() {
        $.ajax({
          url: '/update_spinner_gift_winner',
          type: 'GET',
          data: {
            partner: partner,
            degree: degree
          },
          success: function() {},
        });
      }, 5520);
    },
  });
}

$(document).on('click', '.swal-button--confirm', function() {
  location.reload();
});
