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

def extract_jpg(line)
  fields = line.split(" ")
  return fields[2].split("/",3)[2]
end # extract_jpg
