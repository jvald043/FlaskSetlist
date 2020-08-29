$(document).ready(function(){
  $("#resultSearch").on("keyup", function() {
    var value = $(this).val().toLowerCase();
    console.log(value)
    $("#resultBody tr").filter(function() {
      $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
    });
  });
});
