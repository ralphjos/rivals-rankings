Handlebars.registerHelper('list', function(items, options) {
  var out = '';
  for(var i=0, l=items.length; i<l; i++) {
    var item = items[i];
    var ranking = item.rank;
    var player = item.name;

    var rating = item.rating

    var out = out + "<tr>" + "<td>" + ranking + "</td>" + "<td>" + player + "</td>" + "<td>" + rating + "</td>" + "</tr>";
  }
  return out;
});