require 'Picasa' # https://github.com/morgoth/picasa

class ImagesFromPicasa
  def initialize(password)
    @client = Picasa::Client.new(user_id: "juha.ylitalo@gmail.com", password: password)
    @links = {}
    @album_id = nil
  end # initialize

  def find_album_id(name)
    @client.album.list.entries.each do |album|
      if album.title == name
        @album_id = album.id
        puts "### Found album id ##{@album_id} for #{name}"
        return @album_id
      end # if album.title ...
    end # client.album.list.entries.each

    return nil
  end # find_album_id

  def create_album(name)
    unless self.find_album_id(name).nil?
      puts "### Found existing album #{@album_id}"
      return @album_id
    end

    @album_id = @client.album.create(title: name, access: "public").id
    puts "### Created new album #{@album_id}"
    return @album_id
  end  # create_album

  def _put_photo_into_links(photo)
    resolution="w1280-h800"
    url = photo.media.thumbnails[0].url
    url.sub!(/\/s[0-9]+\//,"/#{resolution}-no/")
    jpg = url.split("/").last
    @links[jpg] = url
  end

  def send_photo(fname)
    puts "### Uploading photo #{fname} to #{@album_id}"
    photo = @client.photo.create(@album_id, file_path: fname)
    self._put_photo_into_links(photo)
  end

  def fetch_links(album)
    links = {}
    album_id = self.find_album_id(album)
    if album_id.nil?
      puts "### No album id found for #{name}"
      exit 3
    end

    @client.album.show(album_id).entries.each do |photo|
      self._put_photo_into_links(photo)
    end # client.album.show().entries
    return links
  end # fetch_links

  def slide2gslide(line)
    jpg = extract_jpg(line).split("/").last
    suffix = nil
    if @links.has_key?(jpg + ".jpg")
      suffix = ".jpg"
    elsif @links.has_key?(jpg + ".JPG")
      suffix = ".JPG"
    else
      puts "Unable to find G+ image for #{jpg}"
      return line
    end # if

    if line.start_with?("{% slide /images")
      line.sub! "{% slide ", "{% gslide "
      line.sub! " %}", " #{@links[jpg + suffix]} %}"
    end # if
    @links.delete(jpg + suffix)
    return line
  end # slide2gslide
end # class ImagesFromPicasa

def find_post(name)
  fnames = Dir.glob("_posts/*[0-9]-#{name}.markdown")
  if fnames.length == 0
    puts "No matching article found (searched for *[0-9]-#{name}.markdown"
    exit 1
  elsif fnames.length > 1
    puts "Found more than one match (searched for *-#{name}.markdown and found #{fnames})"
    exit 2
  end
  puts "### Found #{fnames[0]}"
  return fnames[0]
end # find_post

def find_album_name(post)
  fin = File.open(post)
  fin.each_line do |line|
    if line.start_with?("<!-- G+: ")
      fin.close
      return line.split(" ")[2..-2].join(" ")
    end # if
  end # fin.each_line
  fin.close
end # find_album_name

def extract_jpg(line)
  fields = line.split(" ")
  return fields[2].split("/",3)[2]
end # extract_jpg
