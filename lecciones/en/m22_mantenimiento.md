---
module: 22
---

## In 30 seconds

- A server can decide **who gets in and to what**. A read only role is created and asked to delete.
- It cannot: `permission denied for table lecturas`. A permission never seen refusing does not count.
- The database's backup weighs **22.2 MB**, twelve times less than the table inside the server.
- And it gets really restored, into another database, comparing **count and fingerprint** table by table.
- Both match, and so do the **12** guards. That is now a backup.

## What this module solves

What remains is the two things a file cannot do and the reasons a server gets set up.

The first is **who**. A Parquet is readable by anybody reaching the folder, and there is no way to
let a client look without being able to touch. The second is **going back**: if the disk breaks, a
lake gets remade by running the pipeline, but a database with six months of writes does not.

Both are solved with one line commands. This module teaches something else: **neither is worth
anything until you check it**, and checking costs more work than granting.

## Before the theory: a toy example

The laboratory keeps its certificates in a shared folder. Two problems, one a week.

**The first is about permissions.** The client asks to see their certificates, so somebody gives
them access to the folder. Now the client can see everybody else's, and can delete. Nobody wanted
that: what was wanted was "read, and only their own", and a folder cannot say that.

**The second is about backups.** There has been an automatic backup every night for two years. The
day the disk fails, it turns out the backup has spent fourteen months saving **an empty folder**,
because somebody renamed the good one and nobody noticed.

Notice the second problem cannot be spotted by looking at the backup. It gets spotted by
**restoring it**, and that is the only test there is. A backup nobody has restored is not a backup:
it is a file a lot is expected of.

## Glossary

- **Role.** A user of the database, or a group. In PostgreSQL they are the same thing.
- **`GRANT`.** Giving one specific permission on one specific object.
- **Dump.** The file `pg_dump` produces: the commands and data needed to rebuild the database from
  scratch.
- **`pg_restore`.** What reads that file and rebuilds.
- **Fingerprint.** Here, a few counts over a table's contents. They let two copies be compared
  without going row by row.
- **Disaster recovery.** The serious name for having a backup that really restores.

## Step by step

### Step 1. Create a role that can only read

Three permissions and not one more: connect to the database, see the schema and read the tables.
Nothing about writing.

### Step 2. Ask it to delete

And here is the only part that turns the permission into something checked. A connection is opened
**with that role** and a `DELETE` is attempted. If it goes through, the role is decoration.

It is module 16's contract rule and module 20's guards rule, applied to permissions.

### Step 3. Take the backup

`pg_dump` in the custom format, which compresses. Out comes a single file with everything: tables,
data, constraints and indexes.

### Step 4. Restore it into another database

Not over the good one. A new database gets created and the restore goes there, which besides being
the prudent thing is what makes comparing the two possible.

### Step 5. Check it says the same

Count and fingerprint, table by table, plus the number of guards. A restore that loses the
constraints **is not the same database**, even when the rows add up.

## The code, in parts

### Step 6. The role, and what it gets

```postgres
SELECT rolname, rolcanlogin, rolsuper
FROM pg_roles
WHERE rolname IN ('fuelle', 'mirona')
ORDER BY rolname;
```

```anota
pg_roles | another catalogue view. Users are data too
rolcanlogin | whether it can open a connection
rolsuper | whether it is a superuser, meaning whether it skips every permission
```

```salida
 rolname | rolcanlogin | rolsuper
---------+-------------+----------
 fuelle  | t           | t
 mirona  | t           | f
(2 rows)
```

`fuelle` is a superuser because `initdb` created it in module 19. `mirona` is not, and that is what
makes its permissions mean anything: **nothing can be taken away from a superuser.**

### Step 7. Ask it to delete

```python
con = psycopg.connect(f"... user={SOLO_LECTURA} dbname={BASE}")
leyo = con.execute("SELECT count(*) FROM lecturas").fetchone()[0]
try:
    con.execute("DELETE FROM lecturas WHERE day = DATE '2020-06-05'")
    escribio = True
except psycopg.errors.Error as e:
    escribio, error = False, str(e).splitlines()[0]
```

```anota
psycopg.connect(user=...) | a NEW connection with the limited role. The usual one would be testing the superuser
primero lee | to confirm the role is good for something. A role that cannot even read proves nothing
try / except | the delete is attempted expecting it to fail
```

```salida
  un rol de solo lectura, y se le pide que borre:
    lee 1,841,760 filas
    no puede escribir
    permission denied for table lecturas
```

It reads the one million eight hundred thousand rows and cannot delete a single one. **Both halves
are needed**: without the first, a broken role that could not even connect would pass the test.

### Step 8. Back up and restore

```consola
pg_dump    -h localhost -p 5433 -U fuelle -d fuelle -Fc -f fuelle.dump
createdb   -h localhost -p 5433 -U fuelle fuelle_restaurada
pg_restore -h localhost -p 5433 -U fuelle -d fuelle_restaurada fuelle.dump
```

```anota
-Fc | PostgreSQL's own compressed format. The other format is plain text SQL, which is far bulkier
una base nueva | you restore beside the good one, never over it. If the restore goes wrong, nothing has been lost
```

### Step 9. And the check, which is the module

```postgres
SELECT count(*),
       count(*) FILTER (WHERE medido),
       round(sum(oil_temperature)::numeric, 2),
       count(DISTINCT day)
FROM lecturas;
```

```anota
count(*) FILTER (WHERE ...) | counts only the rows that match. It is a short form of module 9's CASE
sum y count DISTINCT | the fingerprint. Two tables with the same count can hold different data; with the same sum and the same days, it stops being coincidence
```

```salida
 count  |  count  |    round    | count
--------+---------+-------------+-------
1841760 | 1504107 | 94224402.00 |   214
(1 row)
```

That row gets asked of both databases and compared. If they do not match, the backup is no good.

## The result, measured

{{FIG:fig_m22_copia_y_restauracion}}

**What we expected.** That the backup would weigh something like the database.

**What came out.** That it weighs **22.2 MB** when the table inside the server takes **267.8**.
Twelve times less, and **nearly the same as the 21.9 MB of Parquet** everything came from,
because both keep only the data, compressed. This lesson used to say "less even than the Parquet",
and that was because the Parquet of back then came out inflated: module 29 corrected it and the
comparison turned around.

There is no magic: the dump keeps the data compressed and **keeps none of the machinery** module 19
was paying for. No write ahead log, no space the table reserves to grow into, no indexes, which get
rebuilt on restore.

And the check:

| What gets compared | Original | Restored |
|---|---|---|
| rows in `lecturas` | 1,841,760 | 1,841,760 |
| the ones with a measurement | 1,504,107 | 1,504,107 |
| sum of the oil | 94,224,402.00 | 94,224,402.00 |
| distinct days | 214 | 214 |
| rows in `dias` | 214 | 214 |
| **guards** | **12** | **12** |

**The guards are the row almost nobody looks at.** A restore can bring every row across and leave
the constraints behind, and the result looks very much like the good database until the day
somebody writes something impossible. That is why they get counted.

**What it means.** That there is a backup now, and there was not before. The file existed from the
moment `pg_dump` ran. Restoring it and checking is what turns it into a backup.

Restoring costs about twenty five seconds here, and that is the important half: **backing up is
what everybody does and restoring is what almost nobody tests.**

## Watch out

- **A backup never restored is not a backup.** It is the module's line and it is not rhetoric: the
  only way to know it works is to use it.
- **Check the guards and the indexes too.** Counting rows is not enough. A database restored
  without its constraints behaves fine until the first impossible datum.
- **Restore beside, never over.** If the restore fails halfway and it was over the good database,
  you caused the disaster yourself.
- **Nothing can be taken away from a superuser.** If the read only role is a superuser, the
  `GRANT`s do nothing and the test passes for the wrong reason.
- **`-Fc` and not plain SQL.** The custom format compresses and also allows restoring a single
  table. Text SQL is readable and several times heavier.
- **The backup goes elsewhere.** Here it lives in `lake/`, the same folder you want to save. In
  production that is not a backup, it is a copy.

## Metallurgical bridge

Every plant has an emergency plan and a standby generator. And in every serious plant, somebody is
obliged to **start that generator once a month**, with the plant running and with no need for it.

It is not done for fun. It is done because a generator three years without starting has degraded
diesel, a dead battery, or a fuse somebody took for something else. On paper it is there; the day
the grid drops, it does not start.

The monthly test is exactly `pg_restore`. And the fingerprint comparison is the technician checking
something more: the generator does not only start, **it delivers the voltage it should**.

## Review

### What it takes for a read only role to mean anything

That it is not a superuser, and that it gets only the permissions it needs: connect, see the schema
and read the tables. And then, trying to write with it. If the `DELETE` goes through the role is
decoration, and that is only found out by trying.

### Why the backup weighs twelve times less than the server's table

Because it keeps the data compressed and none of the server's machinery. Out goes the write ahead
log, out goes the space reserved to grow into, and out go the indexes, which get rebuilt on
restore. Those 267.8 MB of table were mostly that.

### What gets compared to call a restore good

Content and structure. The row count, some sum and some count of distinct values, which together
act as a fingerprint, and also the number of constraints. A database with the same rows but without
its guards is not the same database.

### Why the restore goes into a new database and not over the usual one

Because a restore that fails halfway leaves the database wrecked, and if it was the good one you
caused the disaster yourself by testing. Beside it, the two can be compared, which is exactly what
is needed to know whether the backup works.

### You have been backing up every night for two years. How many of them work

None that anybody knows of. Until one is restored and compared, what you have is files with the
name of a backup. The usual case is not a failure: they have spent months saving something that no
longer matters, and nobody looks because the process throws no error.
